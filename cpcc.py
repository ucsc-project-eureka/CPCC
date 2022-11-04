#!/usr/bin/env python

""" cpcc.py: Cloud Provider Cost Calculator"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

__author__ = "Tyler Morton"
__copyright__ = "Copyright 2022, Santa Cruz"
__email__ = "tbmorton@ucsc.edu"
__status__ = "Development"

class GraphPage():
    """ Description """
    def __init__(self, row = 2):
        self.row = row
        self.fig = make_subplots(
            rows= row,
            subplot_titles = (
                "Used Storage by Month", "Storage costs",
                "Transaction costs (writes)", "Combined")
        )
        self.count = 0
    def add_plot(self, x, y, layer=False, name = "trace", idx = None, group = "group", dash = 'solid'):
        """Adds a generated line plot to GraphPage figure"""
        if layer:
            self.count = self.count - 1
        self.count = self.count + 1 if idx is None else self.count
        idx = idx if idx is not None else self.count - 1
        row = idx + 1
        self.fig.add_trace(
            go.Scatter(
                x=x, y=y, name=name,
                legendgroup=group,
                legendgrouptitle_text=f"{group}",
                line = dict(dash=dash)
                ), row=row, col=1
        )
    def show(self):
        """Displays subplots"""
        self.fig.show()

class CloudProvider():
    """Definition"""
    def __init__(self, name: str, lifetime: list, used_storage: list):
        self.name = name
        self.title = f'[{self.name}] Total cost of storage over time'
        self.lifetime = lifetime
        self.storage = used_storage
        self.cost = []

    def tiered_storage(self, charge: float, idx: int, prices) -> float:
        """ Calculates storage data costs of a cloud provider that uses tiered rates"""
        acc_charge = 0
        if self.storage[idx]*10**3 < prices[0]:
            acc_charge = charge + prices[0] * self.storage[idx]
        elif self.storage[idx]*10**3 <= prices[1]:
            acc_charge = charge + prices[1] * self.storage[idx]
        else:
            acc_charge = charge + prices[2] * self.storage[idx]
        return acc_charge

    def std_rate_storage(self, charge: float, idx: int, prices) -> float:
        """Calculates storage data costs of a cloud provider that uses a flat rate"""
        return charge + prices[0] * self.storage[idx]

    def storage_cost_data(self, prices):
        """Calculates accumulated cost of using specified cloud provider storage"""
        acc_charge = 0
        tier = False if len(prices) == 1 else True
        for i in range(len(self.lifetime)):
            if tier:
                acc_charge = self.tiered_storage(acc_charge, i, prices)
            else:
                acc_charge = self.std_rate_storage(acc_charge, i, prices)
            self.cost.append(acc_charge)
        return (self.lifetime, self.cost)

    def transaction_cost_data(self, trans, pricing):
        """Calculates cost of specified cloud system based off transactions"""
        acc_pricing = 0
        cost = []
        for _ in self.lifetime:
            acc_pricing = acc_pricing + pricing * (trans * 30) / 10000
            cost.append(acc_pricing)
        return (self.lifetime, cost)
    def total_cost_plot(self):
        """Not implemented"""
        return

# Constants
ROUND_TIME = 5 # in minutes
NODE_DATA_RATE = 0.288
NODE_COUNT = 15 # avg nodes in a cluster
CLUSTER_COUNT = 3 # avg number of clusters in Eureka
NODE_DAY_RATE = NODE_DATA_RATE * 60 * 24
NODE_MONTH_RATE = NODE_DAY_RATE * 30
NODE_YEAR_RATE = NODE_MONTH_RATE * 12
TRANS_DAY_RATE = (60 // ROUND_TIME) * 24
DEPLOYMENT_YEARS = 5

months_arr = [i for i in range(1, DEPLOYMENT_YEARS * 12)]
storage_used = []
storage = 0
for month in months_arr:
    storage = storage + (NODE_MONTH_RATE * NODE_COUNT * CLUSTER_COUNT)/10**6
    storage_used.append(storage)
df = pd.DataFrame(
  dict(
    x = months_arr,
    y = storage_used
  )
)
info_page = GraphPage(4)
info_page.add_plot(months_arr, storage_used)
STORAGE = "Storage"
TRANSACTIONS = "Transactions"
def plot_storage(infopage, cloudprovider, stor_data, group):
    """plots storage cost of provider"""
    stor_data = cloudprovider.storage_cost_data(stor_data)
    infopage.add_plot(stor_data[0], stor_data[1], idx = 1, name=cloudprovider.name, group=group)
    return stor_data[1]

def plot_transaction(infopage, cloudprovider, trans_data, group, trans = TRANS_DAY_RATE):
    """plots transaction cost of provider"""
    trans_data = cloudprovider.transaction_cost_data(trans, trans_data)
    infopage.add_plot(trans_data[0], trans_data[1], idx = 2, name=cloudprovider.name, group=group)
    return trans_data[1]

# storage rates
AWS_S3_STORAGE = (0.026, 0.025, 0.024)
AWS_EBS_STORAGE = 0.12
AWS_EFS_STORAGE =  0.08 # additional charges when accessing infrequent data
AWS_S3_GLACIER_STORAGE = 0.0115
GC_STD_STORAGE = 0.023
GC_NEAR_STORAGE = 0.016
GC_COLD_STORAGE = 0.007
GC_ARCH_STORAGE = 0.0025
# transaction rates
AWS_S3_TRANS = 0.0055
GC_STD_TRANS = 0.05
GC_NEAR_TRANS = 0.10
GC_COLD_TRANS = 0.10 # need to check this
GC_ARCH_TRANS = 0.50
AZURE_HOT_STORAGE = (0.021, 0.02, 0.0191)
AZURE_COLD_STORAGE = (0.0115, 0.0115, 0.0115)
AZURE_ARCHIVE_STORAGE = (0.002, 0.002, 0.002)
AZURE_HOT_TRANS = {"write": 0.072, "read": 0.006, "iter_write": 0.072,
    "iter_read": 0.006, "std" : 0.006}
AZURE_COLD_TRANS= {"write": 0.13, "read": 0.013, "iter_write": 0.13,
    "iter_read": 0.013, "std" : 0.006}
AZURE_ARCHIVE_TRANS = {"write": 0.13, "read": 7.15, "iter_write": 0.143,
    "iter_read": 7.15, "std" : 0.005}
# S3
aws = CloudProvider('simple s3', months_arr, storage_used)
storage = plot_storage(info_page, aws, AWS_S3_STORAGE, STORAGE)

# EBS
aws = CloudProvider('ebs', months_arr, storage_used)
storage = plot_storage(info_page, aws, tuple([AWS_EBS_STORAGE]), STORAGE)

# EFS
aws = CloudProvider('efs', months_arr, storage_used)
storage = plot_storage(info_page, aws, tuple([AWS_EFS_STORAGE]), STORAGE)
# S3 Glacier
aws = CloudProvider('glacier storage', months_arr, storage_used)
storage = plot_storage(info_page, aws, tuple([AWS_S3_GLACIER_STORAGE]), STORAGE)

# standard
google = CloudProvider('gcloud standard', months_arr, storage_used)
storage = plot_storage(info_page, google, tuple([GC_STD_STORAGE]), STORAGE)
trans = plot_transaction(info_page, google, GC_STD_TRANS, TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=google.name, idx = 3)

# nearline
google = CloudProvider('gcloud nearline', months_arr, storage_used)
storage = plot_storage(info_page, google, tuple([GC_NEAR_STORAGE]), STORAGE)
trans = plot_transaction(info_page, google, GC_NEAR_TRANS, TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=google.name, idx = 3)

# coldline
google = CloudProvider('gcloud coldline', months_arr, storage_used)
storage = plot_storage(info_page, google, tuple([GC_COLD_STORAGE]), STORAGE)
trans = plot_transaction(info_page, google, GC_COLD_TRANS, TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=google.name, idx = 3)

# archive
google = CloudProvider('gcloud archive', months_arr, storage_used)
storage = plot_storage(info_page, google, tuple([GC_COLD_STORAGE]), STORAGE)
trans = plot_transaction(info_page, google, GC_COLD_TRANS, TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=google.name, idx = 3)


# hot
azure = CloudProvider('azure hot standard', months_arr, storage_used)
storage = plot_storage(info_page, azure, AZURE_HOT_STORAGE, STORAGE)
trans = plot_transaction(info_page, azure, AZURE_HOT_TRANS["write"], TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=azure.name, idx = 3)

# cool
azure = CloudProvider('azure cold standard', months_arr, storage_used)
storage = plot_storage(info_page, azure, AZURE_COLD_STORAGE, STORAGE)
trans = plot_transaction(info_page, azure, AZURE_COLD_TRANS["write"], TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=azure.name, idx = 3)

# archive
azure = CloudProvider('azure archive standard', months_arr, storage_used)
storage = plot_storage(info_page, azure, AZURE_ARCHIVE_STORAGE, STORAGE)
trans = plot_transaction(info_page, azure, AZURE_ARCHIVE_TRANS["write"], TRANSACTIONS)
combined = np.add(np.array(storage), np.array(trans))
info_page.add_plot(months_arr, combined, False, name=azure.name, idx = 3)
info_page.show()
