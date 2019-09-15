#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 14:35:24 2019

@author: ameanasad
"""

import requests
import json
import numpy as np
import operator


cats =['Food and Dining', 'Shopping',
       'Bills and Utilities', 
       'Transfer', 
       'Auto and Transport',
       'Income', 'Home', 
       'Entertainment', 
       'Taxes',
       'Mortgage and Rent', 
       'Fees and Charges', 'Health and Fitness', 'Travel']


cat_results = {'Food and Dining': 135302, 'Shopping': 31349, 'Bills and Utilities': 11325, 'Transfer': 31691, 'Auto and Transport': 12431, 'Income': 13033, 'Home': 6223, 'Entertainment': 4442, 'Taxes': 1285, 'Mortgage and Rent': 798, 'Fees and Charges': 798, 'Health and Fitness': 1815, 'Travel': 81}



def get_customer_average_spending(customer_id):
    response = requests.get('https://api.td-davinci.com/api/customers/' + customer_id + "/transactions",
        headers = { 'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiYTQ4MjM5ODMtZTExOS0zMDIxLWI1ZDMtZDM3ZDZmM2NjNTgyIiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiIwOGRmYmFhMC03ZWI5LTQxM2ItOGQ0NS0wMGE0NmY4ZTAyYzAifQ.JKMjg-_quhsyB7c0ICdN1u-8yG44wzNlFpNYpCjoR6o' })
    response_data = response.json()
    
    
    data = json.loads(response.text)
    
    results = data['result']
    
    results.sort(key=lambda r: r['originationDateTime'])
    
    monthly_periods = [i for i in range(27,32)]
    amounting_periods = list(map(lambda x: float(len(results)/x), monthly_periods))
    minimization_factor = list(map(lambda x: x-int(x), amounting_periods))
    result_index = minimization_factor.index(min(minimization_factor))   
    period = monthly_periods[result_index]
    iteration_factor = int(amounting_periods[result_index])
    expenditure_mappings = {'Food and Dining': -1.0,
                     'Shopping': -1.0, 
                     'Bills and Utilities': -1.0,
                     'Transfer': -1.0,
                     'Auto and Transport': -1.0, 
                     'Income': 1.0,
                     'Home': -1.0,
                     'Entertainment': -1.0, 
                     'Taxes': -1.0, 
                     'Mortgage and Rent': -1.0, 
                     'Fees and Charges': -1.0,
                     'Health and Fitness': -1.0,
                     'Travel': -1.0,
                     'unknown':-1.0}
   
    categories = {}
    totals =  []
    counter = 0
    
    for i in range(iteration_factor):
        total=0
        for x in range(period):
            try:
                category = results[counter]["categoryTags"][0]    
               
            except:
                category = "unknown"

            
            if category == "Income":
                amount = 0
            else:
                amount = results[counter]['currencyAmount']
            total+=float(abs(amount))
            try:
                categories[category]["Spendings"][str(i)].append(float(abs(amount)))
            except KeyError:
                period_dict = {}
                for z in range(iteration_factor):
                    period_dict[str(z)] = []
                categories[category] = {"Spendings": period_dict}
                categories[category]["Spendings"][str(i)].append(float(abs(amount)))
            counter+=1
            

        totals.append(total)

            
# 
#    print(counter)
#    print(categories)
#    print(totals)
    
    return categories, totals
            
    
    
    


customer = '90f54a9f-9112-451b-b2f9-e5de6b16e0b0'


def get_final_categorization(customer_id):
    customer_categories,totals = get_customer_average_spending(customer_id)
    categories = customer_categories.keys()
    modified_data_category = {}
    
    for key in categories:
        modified_data_category[key] = {"period_totals": []}
        period_list = customer_categories[key]['Spendings']
        period_means = []
        for period in period_list.keys():
            modified_data_category[key]["period_totals"].append(round(sum(period_list[period]),2))
            try:
                period_mean = round(float(sum(period_list[period])/len(period_list[period])),2)      
                period_means.append(period_mean)
            except ZeroDivisionError:
                period_means.append(0)
        try:
            modified_data_category[key]["average_payment"] = round(float(sum(period_means)/len(period_means)),2)
        except ZeroDivisionError:
             modified_data_category[key]["average_payment"] = 0
        
        
        period_totals = np.array(modified_data_category[key]["period_totals"])
        modified_data_category[key]["monthly_average"] = np.mean(period_totals)

        array_totals = np.array(totals)
        average_percentage =  float(sum((period_totals/array_totals))/len(totals))
        
        modified_data_category[key]["average_percentage"] = round(100*average_percentage,2)
        
        final_category = {}
    
        for i in modified_data_category.keys():
            
            if i != "Income":
                final_category[i] = modified_data_category[i]
            else:
                continue
    return final_category


final_cat = get_final_categorization(customer)
           


def get_percentages(final_category):
    keys = []
    percentages = []
    for i in final_category.keys():
        keys.append(i)
        percentages.append(final_category[i]["average_percentage"])
    
    return [keys, percentages]


#print(get_percentages(final_cat))
def get_spending_trends(final_category):
    
    plot_list = []
    for i in list(final_category.keys())[:2]:
        plot_set = {}
        months = [i+1 for i in range(len(final_category[i]["period_totals"]))]
        data = final_category[i]["period_totals"]
        plot_set['title'] = i
        plot_set['months'] = months
        plot_set['data'] =data
        
        plot_list.append(plot_set)
         
    return plot_list

#print(get_spending_trends(final_cat))
        
        



class Savings(object):
   def __init__(self, title, avg_spending, prioritization):
        self.title = title
        self.avg_spending = avg_spending
        self.prioritization = prioritization
        self.priority_ratio = float(avg_spending/prioritization)
   def get_title(self):
        return self.title
    
   def get_spending(self):
        return float(self.avg_spending)
    
   def get_prioritization(self):     
        return float(self.prioritization)
    
   def get_priority_ratio(self):
        return float(self.avg_spending/self.prioritization)
    
   def __str__(self):
       return self.title




    
    
def make_savings_plan(final_categories, priority_mapping, set_amount, periods):
    
    
    saving_per_period = float(set_amount/periods)
    savings = 0
    saving_objects = []
    for i in (final_categories.keys()):
        title = i
        avg_spending = final_categories[i]["average_payment"]
        priority = priority_mapping[i]
        saving_object = Savings(title,avg_spending, priority) 
        saving_objects.append(saving_object)
    
    optimized_saving_options= sorted(saving_objects, key=operator.attrgetter('priority_ratio'))
    
    
    index = 0
    
    saving_plan = {}
    saved_amount = 0

    while(index<len(optimized_saving_options)):
        
        current_saving_option = final_categories[str(optimized_saving_options[index])]
        per_month = current_saving_option["monthly_average"]
        avg_payment =  current_saving_option["average_payment"]
        saved_amount+=per_month
        
        if(float((0.5*saved_amount)/saving_per_period) < 1.0):
            try:
                payment_per_month = 0.5*int((per_month/(avg_payment)))
                amount_per_month = round(payment_per_month*avg_payment,2)
                saving_plan[str(optimized_saving_options[index])] ={"payment_no": payment_per_month, "amount": amount_per_month }
                index+=1
            except ValueError:
                continue
        
        else:
            break
    
    if saving_plan == {}:
        return "Funds are already sufficient to support the given amount"
    if(saved_amount<saving_per_period):
        return "Saving amount not possible given current account status"
    
    
    
    
    return saving_plan
    
    
    
priority_maps = {'Food and Dining': 5,
                 'Shopping': 4, 
                 'Bills and Utilities': 5,
                 'Transfer': 1,
                 'Auto and Transport': 2, 
                 'Income': 4,
                 'Home': 3,
                 'Entertainment': 3, 
                 'Taxes': 3, 
                 'Mortgage and Rent': 2, 
                 'Fees and Charges': 1,
                 'Health and Fitness': 3,
                 'Travel': 1,
                 'unknown':4}

   

n = make_savings_plan(final_cat, priority_maps, 1400, 4)
print(n)



#print(modified_data_category)
#
#print(float(sum(totals)/len(totals)))

# 
#        
#percentage = 0
#pred_tot = [0 for i in range(14)]
#for i in modified_data_category.keys():
#    
#    percentage+=modified_data_category[i]["average_percentage"]
#    
#    length = len(modified_data_category[i]['period_totals'])
#    
#    for x in range(length):
#        m = modified_data_category[i]['period_totals'][x]
#        pred_tot[x]+=m
#    
