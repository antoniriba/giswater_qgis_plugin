'''
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
'''

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QComboBox, QDateEdit, QPushButton, QTableView, QTabWidget, QLineEdit, QDialogButtonBox,  QTextEdit,QPlainTextEdit

from functools import partial

import utils_giswater
from parent_init import ParentDialog
from ui.add_sum import Add_sum          # @UnresolvedImport
from _sqlite3 import Row
from PyQt4.Qt import QDialogButtonBox


def formOpen(dialog, layer, feature):
    ''' Function called when a connec is identified in the map '''
    
    global feature_dialog
    utils_giswater.setDialog(dialog)
    # Create class to manage Feature Form interaction  
    feature_dialog = ManArcDialog(dialog, layer, feature)
    init_config()

    
def init_config():
     
    # Manage 'connecat_id'
    arccat_id = utils_giswater.getWidgetText("arccat_id") 
    utils_giswater.setSelectedItem("arccat_id", arccat_id)   
    
    # Set button signals      
    #feature_dialog.dialog.findChild(QPushButton, "ok").clicked.connect(feature_dialog.save)
    
    feature_dialog.dialog.findChild(QDialogButtonBox, "ok").clicked.connect(feature_dialog.save)            
    #feature_dialog.dialog.findChild(QPushButton, "btn_close").clicked.connect(feature_dialog.close)  


class ManArcDialog(ParentDialog):   
    
    def __init__(self, dialog, layer, feature):
        ''' Constructor class '''
        super(ManArcDialog, self).__init__(dialog, layer, feature)      
        self.init_config_form()
        
        
    def init_config_form(self):
        ''' Custom form initial configuration '''
      
        table_element = "v_ui_element_x_arc" 
        table_document = "v_ui_doc_x_arc"   
        table_event_arc = "v_ui_om_visit_x_arc"

        table_price_arc = "v_price_x_arc"
        
        self.table_varc = self.schema_name+'."v_edit_man_varc"'
        self.table_siphon = self.schema_name+'."v_edit_man_siphon"'
        self.table_conduit = self.schema_name+'."v_edit_man_conduit"'
        self.table_waccel = self.schema_name+'."v_edit_man_waccel"'
        

        # Define class variables
        self.field_id = "arc_id"        
        self.id = utils_giswater.getWidgetText(self.field_id, False)  
        self.filter = self.field_id+" = '"+str(self.id)+"'"                    
        self.connec_type = utils_giswater.getWidgetText("cat_arctype_id", False)        
        self.connecat_id = utils_giswater.getWidgetText("arccat_id", False) 
        
        # Get widget controls      
        self.tab_main = self.dialog.findChild(QTabWidget, "tab_main")  
        self.tbl_element = self.dialog.findChild(QTableView, "tbl_element")   
        self.tbl_document = self.dialog.findChild(QTableView, "tbl_document") 
        self.tbl_event_arc = self.dialog.findChild(QTableView, "tbl_event_arc")  
        self.tbl_price_arc = self.dialog.findChild(QTableView, "tbl_price_arc")
        
        # Load data from related tables
        self.load_data()
        
        # Set layer in editing mode
        # self.layer.startEditing()
        
        # Manage tab visibility
        self.set_tabs_visibility()  
        
        # Fill the info table
        self.fill_table(self.tbl_element, self.schema_name+"."+table_element, self.filter)
        
        # Configuration of info table
        self.set_configuration(self.tbl_element, table_element)    
        
        # Fill the tab Document
        self.fill_tbl_document_man(self.tbl_document, self.schema_name+"."+table_document, self.filter)
        self.tbl_document.doubleClicked.connect(self.open_selected_document)
        
        # Configuration of table Document
        self.set_configuration(self.tbl_document, table_document)
        
        # Fill tab event | arc
        self.fill_tbl_event(self.tbl_event_arc, self.schema_name+"."+table_event_arc, self.filter)
        
        # Configuration of table event | arc
        self.set_configuration(self.tbl_event_arc, table_event_arc)
  
        # Fill tab costs 
        self.fill_costs()
        
        # Fill tab costs | Prices
        self.fill_table(self.tbl_price_arc, self.schema_name+"."+table_price_arc, self.filter)
        
        # Set signals          
        self.dialog.findChild(QPushButton, "btn_doc_delete").clicked.connect(partial(self.delete_records, self.tbl_document, table_document))            
        self.dialog.findChild(QPushButton, "delete_row_info").clicked.connect(partial(self.delete_records, self.tbl_element, table_element))       
        


    def set_tabs_visibility(self):
        ''' Hide some tabs ''' 
          
        # Get schema and table name of selected layer       
        (uri_schema, uri_table) = self.controller.get_layer_source(self.layer)   #@UnusedVariable
        if uri_table is None:
            self.controller.show_warning("Error getting table name from selected layer")
            return
        
        if uri_table == self.table_varc :
            self.tab_main.removeTab(3)
            self.tab_main.removeTab(2)
            self.tab_main.removeTab(0)
            
        if uri_table == self.table_siphon :
            self.tab_main.removeTab(3)
            self.tab_main.removeTab(1)
            self.tab_main.removeTab(0) 
            
        if uri_table == self.table_conduit :
            self.tab_main.removeTab(3)
            self.tab_main.removeTab(2)
            self.tab_main.removeTab(1)
            
        if uri_table == self.table_waccel :
            self.tab_main.removeTab(2)
            self.tab_main.removeTab(1)
            self.tab_main.removeTab(0)
         
       
         
    def fill_costs(self):
        ''' Fill tab costs '''
        
        # Get arc_id
        widget_arc = self.dialog.findChild(QLineEdit, "arc_id")          
        self.arc_id = widget_arc.text()
        
        self.length = self.dialog.findChild(QLineEdit, "length")
        self.budget = self.dialog.findChild(QLineEdit, "budget")
        
        self.arc_cost = self.dialog.findChild(QLineEdit, "arc_cost")
        self.cost_unit = self.dialog.findChild(QLineEdit, "cost_unit")
        self.arc_cost_2 = self.dialog.findChild(QLineEdit, "arc_cost_2")
        self.m2bottom_cost = self.dialog.findChild(QLineEdit, "m2bottom_cost")
        self.m3protec_cost = self.dialog.findChild(QLineEdit, "m3protec_cost")
        self.m3exc_cost = self.dialog.findChild(QLineEdit, "m3exc_cost")
        self.m3fill_cost = self.dialog.findChild(QLineEdit, "m3fill_cost")
        self.m3excess_cost = self.dialog.findChild(QLineEdit, "m3excess_cost")
        self.m2trenchl_cost = self.dialog.findChild(QLineEdit, "m2trenchl_cost")
        self.m2pavement_cost = self.dialog.findChild(QLineEdit, "m2pavement_cost")
        self.m2mlbottom = self.dialog.findChild(QLineEdit, "m2mlbottom")
        self.m3mlprotec = self.dialog.findChild(QLineEdit, "m3mlprotec")
        self.m3mlexc = self.dialog.findChild(QLineEdit, "m3mlexc")
        self.m3mlfill = self.dialog.findChild(QLineEdit, "m3mlfill")
        self.m3mlexcess = self.dialog.findChild(QLineEdit, "m3mlexcess")
        self.m2mltrenchl = self.dialog.findChild(QLineEdit, "m2mltrenchl_2")
        self.m2mlpavement = self.dialog.findChild(QLineEdit, "m2mlpavement")
        self.base_cost = self.dialog.findChild(QLineEdit, "base_cost")
        self.protec_cost = self.dialog.findChild(QLineEdit, "protec_cost")
        self.exc_cost = self.dialog.findChild(QLineEdit, "exc_cost")
        self.fill_cost = self.dialog.findChild(QLineEdit, "fill_cost")
        self.excess_cost = self.dialog.findChild(QLineEdit, "excess_cost")
        self.trenchl_cost = self.dialog.findChild(QLineEdit, "trenchl_cost")
        self.pav_cost = self.dialog.findChild(QLineEdit, "pav_cost")   
        self.cost = self.dialog.findChild(QLineEdit, "cost")     
        
        
        self.z1 = self.dialog.findChild(QLineEdit, "z1")
        self.z2 = self.dialog.findChild(QLineEdit, "z2")
        self.bulk = self.dialog.findChild(QLineEdit, "bulk")
        self.bulk_2 = self.dialog.findChild(QLineEdit, "bulk_2")
        self.bulk_3 = self.dialog.findChild(QLineEdit, "bulk_3")
        self.geom1 = self.dialog.findChild(QLineEdit, "geom1")
        self.b = self.dialog.findChild(QLineEdit, "b")
        self.b_2 = self.dialog.findChild(QLineEdit, "b_2")
        self.y_param = self.dialog.findChild(QLineEdit, "y_param")
        self.m3mlfill_2 = self.dialog.findChild(QLineEdit, "m3mlfill_2")
        self.m3mlexc_2 = self.dialog.findChild(QLineEdit, "m3mlexc_2")
        self.m3mlexcess_2 = self.dialog.findChild(QLineEdit, "m3mlexcess_2")
        self.m2mltrenchl = self.dialog.findChild(QLineEdit, "m2mltrenchl")
        self.m2trenchl_cost_2 = self.dialog.findChild(QLineEdit, "m2trenchl_cost_2")
        self.calculed_y = self.dialog.findChild(QLineEdit, "calculed_y")  
        self.thickness = self.dialog.findChild(QLineEdit, "thickness")
        
        # Get values from database        
        sql = "SELECT *"
        sql+= " FROM "+self.schema_name+".v_plan_cost_arc" 
        sql+= " WHERE arc_id = '"+self.arc_id+"'"    
        row = self.dao.get_row(sql)
        
        self.arc_cost.setText(str(row['arc_cost']))      
        self.cost_unit.setText(str(row['cost_unit'])) 
        self.arc_cost_2.setText(str(row['arc_cost'])) 
        self.m2bottom_cost.setText(str(row['m2bottom_cost'])) 
        self.m2mlbottom.setText(str(row['m2mlbottom'])) 
        self.m3protec_cost.setText(str(row['m3protec_cost'])) 
        self.m3exc_cost.setText(str(row['m3exc_cost'])) 
        self.m3excess_cost.setText(str(row['m3excess_cost'])) 
        self.m3fill_cost.setText(str(row['m3fill_cost'])) 
        self.m3mlexcess.setText(str(row['m3mlexcess'])) 
        self.m2trenchl_cost.setText(str(row['m2trenchl_cost'])) 
        self.m2mltrenchl.setText(str(row['m2mltrenchl'])) 
        self.m3mlprotec.setText(str(row['m3mlprotec'])) 
        self.m3mlexc.setText(str(row['m3mlexc'])) 
        self.m3mlfill.setText(str(row['m3mlfill'])) 
        self.base_cost.setText(str(row['base_cost'])) 
        self.protec_cost.setText(str(row['protec_cost'])) 
        self.exc_cost.setText(str(row['exc_cost'])) 
        self.fill_cost.setText(str(row['fill_cost'])) 
        self.excess_cost.setText(str(row['excess_cost'])) 
        self.trenchl_cost.setText(str(row['trenchl_cost'])) 
        self.pav_cost.setText(str(row['pav_cost']))   
        self.cost.setText(str(row['cost']))  
        self.m2pavement_cost.setText(str(row['m2pav_cost']))  
        self.m2mlpavement.setText(str(row['m2mlpav']))  
        
        self.z1.setText(str(row['z1']))
        self.z2.setText(str(row['z2']))
        self.bulk.setText(str(row['bulk']))
        self.bulk_2.setText(str(row['bulk']))
        self.bulk_3.setText(str(row['bulk']))
        self.geom1.setText(str(row['geom1']))
        self.b.setText(str(row['b']))
        self.b_2.setText(str(row['b']))
        self.y_param.setText(str(row['y_param']))
        self.m3mlfill_2.setText(str(row['m3mlfill']))
        self.m3mlexc_2.setText(str(row['m3mlexc']))
        self.m3mlexcess_2.setText(str(row['m3mlexcess']))
        self.m2mltrenchl.setText(str(row['m2mltrenchl']))
        self.thickness.setText(str(row['thickness']))
        #self.m2trenchl_cost_2.setText(str(row['m2trenchl_cost']))
        self.calculed_y.setText(str(row['calculed_y'])) 


        # Get values from database        
        sql = "SELECT length,budget"
        sql+= " FROM "+self.schema_name+".v_plan_arc" 
        sql+= " WHERE arc_id = '"+self.arc_id+"'"    
        row = self.dao.get_row(sql)
        
        self.length.setText(str(row['length'])) 
        self.budget.setText(str(row['budget'])) 
        

        # Get arccat_id and soilcat_id from v_plan_cost_arc
        sql = "SELECT arccat_id FROM "+self.schema_name+".v_plan_cost_arc WHERE arc_id = '"+self.arc_id+"'" 
        row = self.dao.get_row(sql)
        arccat_id = row[0]

        sql = "SELECT soilcat_id FROM "+self.schema_name+".v_plan_cost_arc WHERE arc_id = '"+self.arc_id+"'" 
        row = self.dao.get_row(sql)
        soilcat_id = row[0]

        
        # Fill QLineEdit -> Arccat
        sql = "SELECT descript FROM "+self.schema_name+".v_price_x_arc WHERE arc_id = '"+self.arc_id+"' AND catalog_id = '"+arccat_id+"'" 
        rows = self.dao.get_rows(sql)
        
        arc_element_value = rows[0]
        arc_bottom_value = rows[1]
        arc_protection_value = rows[2]
        
        arc_element = self.dialog.findChild(QLineEdit, "arc_element")
        arc_bottom = self.dialog.findChild(QLineEdit, "arc_bottom")
        arc_protection = self.dialog.findChild(QLineEdit, "arc_protection")
        
        arc_element.setText(str(arc_element_value[0]))
        arc_bottom.setText(str(arc_bottom_value[0]))
        arc_protection.setText(str(arc_protection_value[0]))
        
        
        # Fill QLineEdit -> Soilcat
        sql = "SELECT descript FROM "+self.schema_name+".v_price_x_arc WHERE arc_id = '"+self.arc_id+"' AND catalog_id = '"+soilcat_id+"'" 
        rows = self.dao.get_rows(sql)
        
        soil_excavation_value = rows[0]
        soil_filling_value = rows[1]
        soil_excess_value = rows[2]
        soil_trenchlining_value = rows[3]
        
        soil_excavation = self.dialog.findChild(QLineEdit, "soil_excavation")
        soil_filling = self.dialog.findChild(QLineEdit, "soil_filling")
        soil_excess = self.dialog.findChild(QLineEdit, "soil_excess")
        soil_trenchlining = self.dialog.findChild(QLineEdit, "soil_trenchlining")
        
        soil_excavation.setText(str(soil_excavation_value[0]))
        soil_filling.setText(str(soil_filling_value[0]))
        soil_excess.setText(str(soil_excess_value[0]))
        soil_trenchlining.setText(str(soil_trenchlining_value[0]))
        
        