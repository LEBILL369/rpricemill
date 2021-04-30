# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date,datetime 
class VehicleIndent(Document):
	def on_submit(self):		
		fuel = 0 
		fuel_expense = 0
		supplier = ""
		service = []
		account = []
		date_ = datetime.now()
		date_ = date_.date()
		for details in self.vehicle_indent_details:
			account = []
			if not details.expense:
				frappe.throw("Please enter expense and quantity")
			if details.service_item == "Fuel":
				fuel = details.qty
				fuel_expense = details.expense
				supplier = details.party
			else:
				service.append({"service_item" : details.service_item, "type" : details.type, "frequency" : details.frequency, "expense_amount" : details.expense})
			service_account = frappe.db.sql("""select sca.account from `tabVehicle Log Property` as vlp inner join `tabSalary Component Account` as sca on sca.parent = vlp.name where vlp.name = %s and sca.company = %s""",(details.service_item,self.company))
			account.append({"account" : details.account,"party_type" : details.party_type,"party":details.party,"branch":self.branch,"cost_center":self.cost_center,"credit_in_account_currency":details.expense})
			if len(service_account):
				account.append({"account" : service_account[0][0],"branch":self.branch,"debit_in_account_currency":details.expense,"cost_center":self.cost_center})
			else:
				frappe.throw("Please Provide Company Account Details for <b>" + str(details.service_item)+"</b> in <b>  Vehicle Log Property </b> ")
			create_journal_entry(self.company,account,date_)
		vehicle_log = frappe.get_doc({
			"doctype" : "Vehicle Log",
			"license_plate" : self.vehicle,
			"employee" : self.driver,
			"date" : date_,
			"odometer" : self.current_odometer_value,
			"fuel_qty" : fuel,
			"price" : fuel_expense,
			"supplier" : supplier,
			"service_detail" : service
		}).submit()
		
def create_journal_entry(company,account,date_):
	journal = frappe.get_doc({
			"doctype" : "Journal Entry",
			"company" : company,
			"posting_date" : date_,
			"accounts" : account
		}).submit()
