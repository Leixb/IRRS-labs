#!/usr/bin/env python
# coding: utf-8

# In[17]:


import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# In[3]:


freq = pd.read_csv("./data/arxiv_abs/frequencies.csv")


# In[8]:


rel_freq = freq.freq / freq.freq[0]


# In[10]:


plt.plot(rel_freq)
plt.yscale("log")


# In[11]:


df = pd.read_csv("./stats.csv")


# In[16]:


plt.scatter(df.max_freq, df.clusters)
plt.xscale("log")


# In[22]:


sns.scatterplot(data=df, x="max_freq", y="clusters", hue="voc_size")
plt.xscale("log")


# In[23]:


sns.scatterplot(data=df, x="max_freq", y="clusters", hue="min_freq")
plt.xscale("log")


# In[25]:


sns.scatterplot(data=df, x="voc_size", y="iter_time")
