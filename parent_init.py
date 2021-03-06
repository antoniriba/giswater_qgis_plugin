'''
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
'''

# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.gui import QgsMessageBar
from PyQt4.Qt import QTableView, QDate
from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import QLabel, QComboBox, QDateEdit, QPushButton, QLineEdit
from PyQt4.QtSql import QSqlTableModel

from functools import partial
import os.path
import sys  
import urlparse
import webbrowser

import utils_giswater
from dao.controller import DaoController
from ui.add_sum import Add_sum          #@UnresolvedImport
        
        
class ParentDialog(object):   
    
    def __init__(self, dialog, layer, feature):
        ''' Constructor class '''     
        self.dialog = dialog
        self.layer = layer
        self.feature = feature
        self.context_name = "ws_parent"    
        self.iface = iface    
        self.init_config()     
        self.set_signals()    
        
        # Set default encoding 
        reload(sys)
        sys.setdefaultencoding('utf-8')   #@UndefinedVariable    
    
        
    def init_config(self):    
     
        # Initialize plugin directory
        cur_path = os.path.dirname(__file__)
        self.plugin_dir = os.path.abspath(cur_path)
        self.plugin_name = os.path.basename(self.plugin_dir) 

        # Get config file
        setting_file = os.path.join(self.plugin_dir, 'config', self.plugin_name+'.config')
        if not os.path.isfile(setting_file):
            message = "Config file not found at: "+setting_file
            self.iface.messageBar().pushMessage(message, QgsMessageBar.WARNING, 20)  
            self.close()
            return
            
        # Set plugin settings
        self.settings = QSettings(setting_file, QSettings.IniFormat)
        self.settings.setIniCodec(sys.getfilesystemencoding())
        
        # Set QGIS settings. Stored in the registry (on Windows) or .ini file (on Unix) 
        self.qgis_settings = QSettings()
        self.qgis_settings.setIniCodec(sys.getfilesystemencoding())  
        
        # Set controller to handle settings and database connection
        self.controller = DaoController(self.settings, self.plugin_name, iface)
        self.controller.set_qgis_settings(self.qgis_settings)  
        status = self.controller.set_database_connection()      
        if not status:
            message = self.controller.last_error
            self.controller.show_warning(message) 
            return 
             
        # Get schema_name and DAO object                
        self.dao = self.controller.dao
        self.schema_name = self.controller.schema_name    
        
        
    def set_signals(self):
        
        try:
            self.dialog.parent().accepted.connect(self.save)
            self.dialog.parent().rejected.connect(self.close)
        except:
            pass
        
            
    def translate_form(self, context_name):
        ''' Translate widgets of the form to current language '''
        # Get objects of type: QLabel
        widget_list = self.dialog.findChildren(QLabel)
        for widget in widget_list:
            self.translate_widget(context_name, widget)
            
            
    def translate_widget(self, context_name, widget):
        ''' Translate widget text '''
        if widget:
            widget_name = widget.objectName()
            text = self.controller.tr(widget_name, context_name)
            if text != widget_name:
                widget.setText(text)         
         
       
    def load_tab_add_info(self):
        ''' Load data from tab 'Add. info' '''                
        pass

    def load_tab_analysis(self):
        ''' Load data from tab 'Analysis' '''          
        pass
                
    def load_tab_document(self):
        ''' Load data from tab 'Document' '''   
        pass
    
    def load_data(self):
        ''' Load data from related tables '''
        self.load_tab_add_info()
        self.load_tab_analysis()
        self.load_tab_document()
        
        
    def save_tab_add_info(self):
        ''' Save tab from tab 'Add. info' '''                
        pass

    def save_tab_analysis(self):
        ''' Save tab from tab 'Analysis' '''          
        pass
                
    def save_tab_document(self):
        ''' Save tab from tab 'Document' '''   
        pass       
                        
    def save_data(self):
        ''' Save data from related tables '''        
        self.save_tab_add_info()
        self.save_tab_analysis()
        self.save_tab_document()  
                
               
    def save(self):
        ''' Save feature '''
        self.save_data()   
        self.dialog.accept()
        self.close()     
        
        
    def close(self):
        ''' Close form without saving ''' 
        self.dialog.parent().setVisible(False)         
        
        
    def set_model_to_table(self, widget, table_name, filter_): 
        ''' Set a model with selected filter.
        Attach that model to selected table '''
        
        # Set model
        model = QSqlTableModel();
        model.setTable(table_name)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)        
        model.setFilter(filter_)

        model.select()         

        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())      

        # Attach model to table view
        widget.setModel(model)    
        
        
    def delete_records(self, widget, table_name):
        ''' Delete selected elements of the table '''

        # Get selected rows
        selected_list = widget.selectionModel().selectedRows()   
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message, context_name='ui_message' ) 
            return
        
        inf_text = ""
        list_doc_id = ""
        row_index = ""
        list_id = ""
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            doc_id_ = widget.model().record(row).value("doc_id")
            id_ = widget.model().record(row).value("id")
            if doc_id_ == None:
                doc_id_ = widget.model().record(row).value("element_id")
            inf_text += str(doc_id_)+", "
            list_id += str(id_)+", "
            list_doc_id = list_doc_id+str(doc_id_)+", "
            row_index += str(row+1)+", "
            
        row_index = row_index[:-2]
        inf_text = inf_text[:-2]
        list_doc_id = list_doc_id[:-2]
        list_id = list_id[:-2]
  
        answer = self.controller.ask_question("Are you sure you want to delete these records?", "Delete records", list_doc_id)
        if answer:
            sql = "DELETE FROM "+self.schema_name+"."+table_name 
            sql+= " WHERE id IN ("+list_id+")"
            self.controller.execute_sql(sql)
            widget.model().select()
 
         
    def delete_records_hydro(self, widget):
        ''' Delete selected elements of the table '''

        # Get selected rows
        selected_list = widget.selectionModel().selectedRows()    
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message, context_name='ui_message' ) 
            return
        
        inf_text = ""
        list_id = ""
        row_index = ""
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = widget.model().record(row).value("hydrometer_id")
            inf_text+= str(id_)+", "
            list_id = list_id+"'"+str(id_)+"', "
            row_index += str(row+1)+", "
            
        row_index = row_index[:-2]
        inf_text = inf_text[:-2]
        list_id = list_id[:-2]

        answer = self.controller.ask_question("Are you sure you want to delete these records?", "Delete records", list_id)
        table_name = '"rtc_hydrometer_x_connec"'
        table_name2 = '"rtc_hydrometer"'
        if answer:
            sql = "DELETE FROM "+self.schema_name+"."+table_name 
            sql+= " WHERE hydrometer_id IN ("+list_id+")"
            self.controller.execute_sql(sql)

            sql = "DELETE FROM "+self.schema_name+"."+table_name2 
            sql+= " WHERE hydrometer_id IN ("+list_id+")"
            self.controller.execute_sql(sql)
            
            widget.model().select()
            
                   
    def insert_records (self):
        ''' Insert value  Hydrometer | Hydrometer'''
        
        # Create the dialog and signals
        self.dlg_sum = Add_sum()
        utils_giswater.setDialog(self.dlg_sum)
        # Set signals
        self.dlg_sum.findChild(QPushButton, "btn_accept").clicked.connect(self.btn_accept)
        self.dlg_sum.findChild(QPushButton, "btn_close").clicked.connect(self.btn_close)
        
        # Open the dialog
        self.dlg_sum.exec_() 
        
        
    def btn_accept(self):
        ''' Save new value oh hydrometer'''
  
        # Get widget text - hydtometer_id
        widget_hydro = self.dlg_sum.findChild(QLineEdit, "hydrometer_id_new")          
        self.hydro_id = widget_hydro.text()

        # Get connec_id       
        widget_connec = self.dialog.findChild(QLineEdit, "connec_id")          
        self.connec_id = widget_connec.text()

        # Check if Hydrometer_id already exists
        sql = "SELECT DISTINCT(hydrometer_id) FROM "+self.schema_name+".rtc_hydrometer WHERE hydrometer_id = '"+self.hydro_id+"'" 
        row = self.dao.get_row(sql)
        if row:
        # if exist - show warning
            self.controller.show_info_box("Hydrometer_id "+self.hydro_id+" exist in data base!", "Info")
        else:
        # in not exist insert hydrometer_id
            # if not exist - insert new Hydrometer id
            # Insert hydrometer_id in v_rtc_hydrometer
            sql = "INSERT INTO "+self.schema_name+".rtc_hydrometer (hydrometer_id) "
            sql+= " VALUES ('"+self.hydro_id+"')"
            self.controller.execute_sql(sql) 
            
            # insert hydtometer_id and connec_id in rtc_hydrometer_x_connec
            sql = "INSERT INTO "+self.schema_name+".rtc_hydrometer_x_connec (hydrometer_id, connec_id) "
            sql+= " VALUES ('"+self.hydro_id+"','"+self.connec_id+"')"
            self.controller.execute_sql(sql) 
        
            # Refresh table in Qtableview
            # Fill tab Hydrometer
            table_hydrometer = "v_rtc_hydrometer"
            self.fill_tbl_hydrometer(self.tbl_hydrometer, self.schema_name+"."+table_hydrometer, self.filter)
          
            self.dlg_sum.close()
                
              
    def btn_close(self):
        ''' Close form without saving '''
        self.dlg_sum.close()
          
        
    def open_selected_document(self):
        ''' Get value from selected cell ("PATH")
        Open the document ''' 
        
        # Check if clicked value is from the column "PATH"
        position_column = self.tbl_document.currentIndex().column()
        if position_column == 4:      
            # Get data from address in memory (pointer)
            self.path = self.tbl_document.selectedIndexes()[0].data()

            # Parse a URL into components
            url = urlparse.urlsplit(self.path)

            # Check if path is URL
            if url.scheme == "http":
                # If path is URL open URL in browser
                webbrowser.open(self.path) 
            else: 
                # If its not URL ,check if file exist
                if not os.path.exists(self.path):
                    message = "File not found!"
                    self.controller.show_warning(message, context_name='ui_message')
                else:
                    # Open the document
                    os.startfile(self.path)   
    
    
    def open_selected_document_event(self):
        ''' Get value from selected cell ("PATH")
        Open the document ''' 
        
        # Check if clicked value is from the column "PATH"
        position_column = self.tbl_event.currentIndex().column()
        if position_column == 7:      
            # Get data from address in memory (pointer)
            self.path = self.tbl_event.selectedIndexes()[0].data()

            sql = "SELECT value FROM "+self.schema_name+".config_param_text"
            sql+= " WHERE id = 'om_visit_absolute_path'"
            row = self.dao.get_row(sql)
            # Full path= path + value from row
            self.full_path = row[0]+self.path
            
            # Parse a URL into components
            url = urlparse.urlsplit(self.full_path)
        
            # Check if path is URL
            if url.scheme == "http":
                # If path is URL open URL in browser
                webbrowser.open(self.full_path) 
            else: 
                # If its not URL ,check if file exist
                if not os.path.exists(self.full_path):
                    message = "File not found!"
                    self.controller.show_warning(message, context_name='ui_message')
                else:
                    # Open the document
                    os.startfile(self.full_path)          
                           
                    
    def open_selected_document_from_table(self):
        ''' Button - Open document from table document'''
        
        self.tbl_document = self.dialog.findChild(QTableView, "tbl_document")
        # Get selected rows
        selected_list = self.tbl_document.selectionModel().selectedRows()    
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message, context_name='ui_message' ) 
            return
        
        inf_text = ""
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = self.tbl_document.model().record(row).value("path")
            inf_text+= str(id_)+", "
        inf_text = inf_text[:-2]
        self.path = inf_text 
        
        sql = "SELECT value FROM "+self.schema_name+".config_param_text"
        sql +=" WHERE id = 'doc_absolute_path'"
        row = self.dao.get_row(sql)
        if row is None:
            message = "Check doc_absolute_path in table config_param_text, value does not exist or is not defined!"
            self.controller.show_warning(message, context_name='ui_message')
            return
        else:
            # Full path= path + value from row
            self.full_path =row[0]+self.path
           
            # Parse a URL into components
            url=urlparse.urlsplit(self.full_path)
    
            # Check if path is URL
            if url.scheme=="http":
                # If path is URL open URL in browser
                webbrowser.open(self.full_path) 
            else: 
                # If its not URL ,check if file exist
                if not os.path.exists(self.full_path):
                    message = "File not found:"+self.full_path 
                    self.controller.show_warning(message, context_name='ui_message')
                       
                else:
                    # Open the document
                    os.startfile(self.full_path)    
                

    def set_filter_table(self, widget):
        ''' Get values selected by the user and sets a new filter for its table model '''
        
        # Get selected dates
        date_from = self.date_document_from.date().toString('yyyyMMdd') 
        date_to = self.date_document_to.date().toString('yyyyMMdd') 
        if (date_from > date_to):
            message = "Selected date interval is not valid"
            self.controller.show_warning(message, context_name='ui_message')                   
            return
        
        # Set filter
        expr = self.field_id+" = '"+self.id+"'"
        expr+= " AND date >= '"+date_from+"' AND date <= '"+date_to+"'"
        
        # Get selected values in Comboboxes        
        doc_type_value = utils_giswater.getWidgetText("doc_type")
        if doc_type_value != 'null': 
            expr+= " AND doc_type = '"+doc_type_value+"'"
        doc_tag_value = utils_giswater.getWidgetText("doc_tag")
        if doc_tag_value != 'null': 
            expr+= " AND tagcat_id = '"+doc_tag_value+"'"
        doc_user_value = utils_giswater.getWidgetText("doc_user")
        if doc_user_value != 'null':
            expr+= " AND user_name = '"+doc_user_value+"'"
  
        # Refresh model with selected filter
        widget.model().setFilter(expr)
        widget.model().select() 
        
        
    def set_filter_table_man(self, widget):
        ''' Get values selected by the user and sets a new filter for its table model '''
        
        # Get selected dates
        date_from = self.date_document_from.date().toString('yyyyMMdd') 
        date_to = self.date_document_to.date().toString('yyyyMMdd') 
        if (date_from > date_to):
            message = "Selected date interval is not valid"
            self.controller.show_warning(message, context_name='ui_message')                   
            return
        
        # Set filter
        expr = self.field_id+" = '"+self.id+"'"
        expr+= " AND date >= '"+date_from+"' AND date <= '"+date_to+"'"
        
        # Get selected values in Comboboxes        
        doc_type_value = utils_giswater.getWidgetText("doc_type")
        if doc_type_value != 'null': 
            expr+= " AND doc_type = '"+doc_type_value+"'"
        doc_tag_value = utils_giswater.getWidgetText("doc_tag")
        if doc_tag_value != 'null': 
            expr+= " AND tagcat_id = '"+doc_tag_value+"'"
  
        # Refresh model with selected filter
        widget.model().setFilter(expr)
        widget.model().select()  
        
        
    def set_configuration(self, widget, table_name):
        ''' Configuration of tables 
        Set visibility of columns
        Set width of columns '''
        
        widget = utils_giswater.getWidget(widget)
        if not widget:
            return        
        
        # Set width and alias of visible columns
        columns_to_delete = []
        sql = "SELECT column_index, width, alias, status"
        sql+= " FROM "+self.schema_name+".config_ui_forms"
        sql+= " WHERE ui_table = '"+table_name+"'"
        sql+= " ORDER BY column_index"
        rows = self.controller.get_rows(sql)
        if not rows:
            return
        
        for row in rows:        
            if not row['status']:
                columns_to_delete.append(row['column_index']-1)
            else:
                width = row['width']
                if width is None:
                    width = 100
                widget.setColumnWidth(row['column_index']-1, width)
                widget.model().setHeaderData(row['column_index']-1, Qt.Horizontal, row['alias'])
    
        # Set order
        widget.model().setSort(0, Qt.AscendingOrder)    
        widget.model().select()

        # Delete columns        
        for column in columns_to_delete:
            widget.hideColumn(column) 


    def fill_tbl_document(self, widget, table_name, filter_):
        ''' Fill the table control to show documents'''

        # Get widgets
        doc_user = self.dialog.findChild(QComboBox, "doc_user")
        doc_type = self.dialog.findChild(QComboBox, "doc_type")
        doc_tag = self.dialog.findChild(QComboBox, "doc_tag")
        self.date_document_to = self.dialog.findChild(QDateEdit, "date_document_to")
        self.date_document_from = self.dialog.findChild(QDateEdit, "date_document_from")

        # Set signals
        doc_user.activated.connect(partial(self.set_filter_table, widget))
        doc_type.activated.connect(partial(self.set_filter_table, widget))
        doc_tag.activated.connect(partial(self.set_filter_table, widget))
        self.date_document_to.dateChanged.connect(partial(self.set_filter_table, widget))
        self.date_document_from.dateChanged.connect(partial(self.set_filter_table, widget))
        #self.tbl_document.doubleClicked.connect(self.open_selected_document)

        # Fill ComboBox tagcat_id
        sql = "SELECT DISTINCT(tagcat_id)"
        sql+= " FROM "+table_name
        sql+= " ORDER BY tagcat_id"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("doc_tag", rows)

        # Fill ComboBox doccat_id
        sql = "SELECT DISTINCT(doc_type)"
        sql+= " FROM "+table_name
        sql+= " ORDER BY doc_type"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("doc_type", rows)

        # Fill ComboBox doc_user
        sql = "SELECT DISTINCT(user_name)"
        sql+= " FROM "+table_name
        sql+= " ORDER BY user_name"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("doc_user", rows)
        
        # Set model of selected widget
        self.set_model_to_table(widget, table_name, filter_)
        
        
    def fill_tbl_document_man(self, widget, table_name, filter_):
        ''' Fill the table control to show documents'''
        
        # Get widgets  
        doc_type = self.dialog.findChild(QComboBox, "doc_type")
        doc_tag = self.dialog.findChild(QComboBox, "doc_tag")
        self.date_document_to = self.dialog.findChild(QDateEdit, "date_document_to")
        self.date_document_from = self.dialog.findChild(QDateEdit, "date_document_from")
        date = QDate.currentDate();
        self.date_document_to.setDate(date);

           
        self.btn_open_path = self.dialog.findChild(QPushButton,"btn_open_path")
        self.btn_open_path.clicked.connect(self.open_selected_document_from_table) 
        
        # Set signals
        doc_type.activated.connect(partial(self.set_filter_table_man, widget))
        doc_tag.activated.connect(partial(self.set_filter_table_man, widget))
        self.date_document_to.dateChanged.connect(partial(self.set_filter_table_man, widget))
        self.date_document_from.dateChanged.connect(partial(self.set_filter_table_man, widget))
        #self.tbl_document.doubleClicked.connect(self.open_selected_document)

        # Fill ComboBox tagcat_id
        sql = "SELECT DISTINCT(tagcat_id)"
        sql+= " FROM "+table_name
        sql+= " ORDER BY tagcat_id"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("doc_tag", rows)

        # Fill ComboBox doccat_id
        sql = "SELECT DISTINCT(doc_type)"
        sql+= " FROM "+table_name
        sql+= " ORDER BY doc_type"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("doc_type", rows)

        # Set model of selected widget
        self.set_model_to_table(widget, table_name, filter_)
    

    def fill_table(self, widget, table_name, filter_): 
        ''' Fill info tab of node '''
        self.set_model_to_table(widget, table_name, filter_)     
        
             
    def fill_tbl_event(self, widget, table_name, filter_):
        ''' Fill the table control to show documents'''
        
        #table_name_event_type = self.schema_name+'."om_visit_parameter_type"'
        table_name_event_id = self.schema_name+'."om_visit_parameter"'
        
        # Get widgets  
        event_type = self.dialog.findChild(QComboBox, "event_type")
        event_id = self.dialog.findChild(QComboBox, "event_id")
        self.date_event_to = self.dialog.findChild(QDateEdit, "date_event_to")
        self.date_event_from = self.dialog.findChild(QDateEdit, "date_event_from")
        date = QDate.currentDate();
        self.date_event_to.setDate(date);


        # Set signals
        event_type.activated.connect(partial(self.set_filter_table_event, widget))
        event_id.activated.connect(partial(self.set_filter_table_event2, widget))
        self.date_event_to.dateChanged.connect(partial(self.set_filter_table_event, widget))
        self.date_event_from.dateChanged.connect(partial(self.set_filter_table_event, widget))
    
        feature_key = self.controller.get_layer_source_key()
        if feature_key == 'node_id':
            feature = 'NODE'
        if feature_key == 'connec_id':
            feature = 'CONNEC'
        if feature_key == 'arc_id':
            feature = 'ARC'
        if feature_key == 'gully_id':
            feature = 'GULLY'
             
        # Fill ComboBox event_id
        sql = "SELECT DISTINCT(id)"
        sql+= " FROM "+table_name_event_id
        sql+= " WHERE feature = '"+feature+"' OR feature = 'ALL'" 
        sql+= " ORDER BY id"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("event_id", rows)
           

        # Fill ComboBox event_type
        sql = "SELECT DISTINCT(parameter_type)"
        sql+= " FROM "+table_name_event_id
        sql+= " WHERE feature = '"+feature+"' OR feature = 'ALL'" 
        sql+= " ORDER BY parameter_type"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("event_type", rows)
        
        # Set model of selected widget
        self.set_model_to_table(widget, table_name, filter_)    
                   
    
    def set_filter_table_event(self, widget):
        ''' Get values selected by the user and sets a new filter for its table model '''

        # Get selected dates
        date_from = self.date_event_from.date().toString('yyyyMMdd') 
        date_to = self.date_event_to.date().toString('yyyyMMdd') 
        if (date_from > date_to):
            message = "Selected date interval is not valid"
            self.controller.show_warning(message, context_name='ui_message')                   
            return
        
        # Cascade filter 
        table_name_event_id = self.schema_name+'."om_visit_parameter"'
        event_type_value = utils_giswater.getWidgetText("event_type")
        # Get type of feature
        feature_key = self.controller.get_layer_source_key()
        if feature_key == 'node_id':
            feature = 'NODE'
        if feature_key == 'connec_id':
            feature = 'CONNEC'
        if feature_key == 'arc_id':
            feature = 'ARC'
        if feature_key == 'gully_id':
            feature = 'GULLY'

        # Fill ComboBox event_id
        sql = "SELECT DISTINCT(id)"
        sql+= " FROM "+table_name_event_id
        sql+= " WHERE (feature = '"+feature+"' OR feature = 'ALL')"
        if event_type_value != 'null':
            sql+= " AND parameter_type= '"+event_type_value+"'" 
        sql+= " ORDER BY id"
        rows = self.dao.get_rows(sql)
        utils_giswater.fillComboBox("event_id", rows)
        # End cascading filter
            
        # Set filter to model
        expr = self.field_id+" = '"+self.id+"'"
        expr += " AND tstamp >= '"+date_from+"' AND tstamp <= '"+date_to+"'"
        
        # Get selected values in Comboboxes        
        event_type_value = utils_giswater.getWidgetText("event_type")
        if event_type_value != 'null': 
            expr+= " AND parameter_type = '"+event_type_value+"'"
        event_id = utils_giswater.getWidgetText("event_id")
        if event_id != 'null': 
            expr+= " AND parameter_id = '"+event_id+"'"
            
        # Refresh model with selected filter
        widget.model().setFilter(expr)
        widget.model().select() 
       
        
    def set_filter_table_event2(self, widget):
        ''' Get values selected by the user and sets a new filter for its table model '''
        ''' Cascading filter '''
        
        # Get selected dates
        date_from = self.date_event_from.date().toString('yyyyMMdd') 
        date_to = self.date_event_to.date().toString('yyyyMMdd') 
        if (date_from > date_to):
            message = "Selected date interval is not valid"
            self.controller.show_warning(message, context_name='ui_message')                   
            return

        # Set filter
        expr = self.field_id+" = '"+self.id+"'"
        expr += " AND tstamp >= '"+date_from+"' AND tstamp <= '"+date_to+"'"
        
        # Get selected values in Comboboxes        
        event_type_value = utils_giswater.getWidgetText("event_type")
        if event_type_value != 'null': 
            expr+= " AND parameter_type = '"+event_type_value+"'"
        event_id = utils_giswater.getWidgetText("event_id")
        if event_id != 'null': 
            expr+= " AND parameter_id = '"+event_id+"'"
            
        # Refresh model with selected filter
        widget.model().setFilter(expr)
        widget.model().select() 
        
        
    def fill_tbl_hydrometer(self, widget, table_name, filter_):
        ''' Fill the table control to show documents'''

        # Get widgets  
        self.date_el_to = self.dialog.findChild(QDateEdit, "date_el_to")
        self.date_el_from = self.dialog.findChild(QDateEdit, "date_el_from")
        date = QDate.currentDate();
        self.date_el_to.setDate(date);

        # Set signals
        self.date_el_to.dateChanged.connect(partial(self.set_filter_hydrometer, widget))
        self.date_el_from.dateChanged.connect(partial(self.set_filter_hydrometer, widget))
        #self.tbl_document.doubleClicked.connect(self.open_selected_document)

        # Set model of selected widget
        self.set_model_to_table(widget, table_name, filter_)
        
        
    def set_filter_hydrometer(self, widget):
        ''' Get values selected by the user and sets a new filter for its table model '''

        # Get selected dates
        date_from = self.date_el_from.date().toString('yyyyMMdd') 
        date_to = self.date_el_to.date().toString('yyyyMMdd') 
        if (date_from > date_to):
            message = "Selected date interval is not valid"
            self.controller.show_warning(message, context_name='ui_message')                   
            return
        
        # Set filter
        expr = self.field_id+" = '"+self.id+"'"
        expr+= " AND date >= '"+date_from+"' AND date <= '"+date_to+"'"
  
        # Refresh model with selected filter
        widget.model().setFilter(expr)
        widget.model().select() 
        
        
    def set_tabs_visibility(self,num_el):
        ''' Hide some tabs '''   

        for i in xrange(num_el,-1,-1):
            # Get name of selected layer 
            selected_layer = self.layer.name() 
            # Get name of current tab
            tab_text = self.tab_main.tabText(i)
            if selected_layer != tab_text :
                self.tab_main.removeTab(i) 
                
                
    def setImage(self, widget):
        
        # Manage 'cat_shape'
        arc_id = utils_giswater.getWidgetText("arc_id") 
        cur_layer = self.iface.activeLayer()  
        table_name = self.controller.get_layer_source_table_name(cur_layer) 
        column_name = cur_layer.name().lower()+"_cat_shape"
    
        # Get cat_shape value from database       
        sql = "SELECT "+column_name+"" 
        sql+= " FROM "+self.schema_name+"."+table_name+""
        sql+= " WHERE arc_id = '"+arc_id+"'"
        row = self.dao.get_row(sql)

        if row is not None:
            if row[0] != 'VIRTUAL': 
                utils_giswater.setImage(widget, row[0])
            # If selected table is Virtual hide tab cost
            else :
                self.tab_main.removeTab(4)       

        