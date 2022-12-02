import json
import numpy as np
import pandas as pd
import json
import datetime as dt

def get_customers():
    customers = pd.read_json('Customers.json', orient='columns')
    customers = customers[['billwerk_id', 'pipedrive_id']]
    customers.columns = ['CustomerId', 'PipedriveId']
    customers = customers.dropna()
    customers = customers.drop_duplicates()


    return customers


def merge_contracts(customers):
    contracts = pd.read_csv('contracts-20220423.csv')
    contracts = contracts[['CustomerId', 'ContractStartDateUtc', 'ContractEndDateUtc', 'FirstPlanVariantId']]
    contracts['Churned'] = np.where(contracts['ContractEndDateUtc'].isnull(), 0, 1)
    contracts['ContractEndDateUtc'].fillna(value=pd.to_datetime('4/1/2022'), inplace=True)
    contracts['ContractStartDateUtc'] = pd.to_datetime(contracts['ContractStartDateUtc'], utc=True)
    contracts['ContractEndDateUtc'] = pd.to_datetime(contracts['ContractEndDateUtc'], utc=True)
    contracts = contracts[contracts.ContractEndDateUtc < pd.to_datetime('4/2/2022', utc=True)]
    contracts['NumberOfDaysActive'] = (contracts['ContractEndDateUtc'] - contracts['ContractStartDateUtc']).dt.days
    
    contracts = contracts.dropna()
    contracts = contracts.drop_duplicates()
    contracts = contracts[contracts.NumberOfDaysActive > 30]

    customers = customers.merge(contracts, left_on='CustomerId', right_on='CustomerId')
    customers = customers[['CustomerId', 'PipedriveId', 'ContractStartDateUtc', 'ContractEndDateUtc', 'FirstPlanVariantId', 'Churned', 'NumberOfDaysActive']]

    return customers


def merge_completed_tasks(customers):
    with open('CompletedTasks.json', 'r') as f:
        data = json.load(f)

    tasks = pd.json_normalize(data)
    tasks.columns = ['CreatedAt', 'task.workout_plan', 'task.title', 'PipedriveId', 'task']
    tasks = tasks[['CreatedAt', 'PipedriveId']]
    tasks['CreatedAt'] = pd.to_datetime(tasks['CreatedAt'], utc=True)
    tasks = tasks.dropna()

    customers = customers.merge(tasks, how='left', left_on='PipedriveId', right_on='PipedriveId' )
    customers = customers.dropna()

    return customers


def get_amount_tasks_last_month(customerId, contractEndDate, customersXtasks):
    amount = 0
    for index, row in customersXtasks.iterrows():
        diff = (contractEndDate - row['CreatedAt']).days
        if diff <= 31:
            amount += 1 

    return amount


def get_amount_tasks(customerId, customersXtasks):
    amount = customersXtasks[customersXtasks.CustomerId == customerId].shape[0]
    
    return amount


def fix_plan_variant(customers):
    plan_variant_id = []
    for index, row in customers.iterrows():
        if row['FirstPlanVariantId'] == '5ee8e2ac6237070d18ade4ee':
            plan_variant_id.append('Pro Plan')
        elif row['FirstPlanVariantId'] == '5f8e8ea23a5ed4dc29b70522':
            plan_variant_id.append('WeightBet')
        else:
            plan_variant_id.append('Basic Plan')

    customers['FirstPlanVariantId'] = plan_variant_id
    return customers


def filter_customers_without_tasks(customers):
    customers = customers[customers.AmountTasksPerMonth > 0]
    return customers


def get_tasks_info(customers, customersXtasks):
    amount_tasks = []
    for index, row in customers.iterrows():
        months = row['NumberOfDaysActive']/30
        amount_tasks.append(get_amount_tasks(row['CustomerId'], customersXtasks)/months)

    customers['AmountTasksPerMonth'] = amount_tasks

    amount_tasks_last_month = []
    for index, row in customers.iterrows():
        amount_tasks_last_month.append(get_amount_tasks_last_month(row['CustomerId'], row['ContractEndDateUtc'], customersXtasks[customersXtasks.CustomerId == row['CustomerId']]))

    customers['AmountTasksLastMonth'] = amount_tasks_last_month
    
    return customers


def main():

    customers = get_customers()
    customers = merge_contracts(customers)

    customersXtasks = merge_completed_tasks(customers)
    #customersXtasks.to_csv('customersXtasks.csv')

    customers = get_tasks_info(customers, customersXtasks)
    customers = fix_plan_variant(customers)
    customers = filter_customers_without_tasks(customers)

    raw_customers = customers.copy()
    raw_customers.Churned = raw_customers.Churned.replace(1, 'Yes')
    raw_customers.Churned = raw_customers.Churned.replace(0, 'No')
    raw_customers.to_csv('../data/raw_customers.csv')

    customers = pd.get_dummies(customers, columns=["FirstPlanVariantId"])
    customers.to_csv('../data/customers.csv')


    print("Total number of non-churners: " + str(customers.shape[0] - customers['Churned'].sum()))
    print("Total number of churners: " + str(customers['Churned'].sum()))
    print("DONE")


main()
