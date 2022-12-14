#!/usr/bin/env python
# coding: utf-8

# In[2]:


import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# In[10]:


sns.set_theme(
    context="paper",
    style="whitegrid",
    font_scale=1.5,
    font="STIXGeneral",
    rc={
        "text.usetex": True,
    },
)
save_args = dict(dpi=300)


# In[3]:


freq = pd.read_csv("./data/arxiv_abs/frequencies.csv")


# In[4]:


rel_freq = freq.freq / freq.freq[0]


# In[5]:


plt.plot(rel_freq)
plt.yscale("log")


# In[7]:


plt.plot(freq.freq)
plt.yscale("log")
plt.xscale("log")


# In[ ]:


plt.save()


# In[207]:


df2 = pd.read_csv("./stats2.csv")
df3 = pd.read_csv("./stats3.csv")
df = pd.read_csv("./stats.csv")
(max(df3[df3.it_converged == 1].it_clusters), max(df3[df3.iteration == 20].it_clusters))


# In[209]:


conv = df3[df3.it_converged == 1]

conv[conv.it_clusters >= 3]


# In[213]:


nconv = df3[df3.iteration == 20]
nconv[nconv.it_clusters >= 3]


# In[150]:


df


# In[160]:


sns.scatterplot(data=df2[df2.iteration >= 10], x="actual_words", y="it_clusters")
plt.xscale("log")


# In[183]:


max(df3[df3.it_converged == 1].it_clusters)


# In[177]:


df["clusters_cat"] = df["clusters"].astype("string")
sns.stripplot(
    data=df, x="max_freq", y="clusters_cat", hue="voc_size", palette="magma_r"
)
plt.xscale("log")


# In[23]:


sns.scatterplot(data=df, x="max_freq", y="clusters", hue="min_freq")
plt.xscale("log")


# In[25]:


sns.scatterplot(data=df, x="voc_size", y="iter_time")


# In[8]:


import sklearn

# In[46]:


df_100 = pd.read_csv("./ncores_100_0.01_0.02.csv")


# In[47]:


df_250 = pd.read_csv("./ncores_250_0.01_0.02.csv")


# In[48]:


df_100


# In[147]:


sns.lineplot(
    data=df_time[df_time["iteration"] != 1],
    x="ncores",
    y="time",
    hue="cluster_size_cat",
)
plt.xlabel("Number of cores")
plt.ylabel("Execution time (ms)")
plt.legend(title="Vocabulary size")
plt.ylim(0, None)
plt.savefig("figures/ex-cores.pdf", **save_args)


# In[148]:


sns.lineplot(data=df_time, x="iteration", y="time", hue="cluster_size_cat")
plt.ylim(0, None)
plt.xlabel("Iteration")
plt.ylabel("Execution time (ms)")
plt.legend(title="Vocabulary size", loc="lower right")
plt.savefig("figures/ex-iter.pdf", **save_args)


# In[56]:


df_250["cluster_size"] = 250
df_100["cluster_size"] = 100


# In[63]:


df_time = pd.concat([df_100, df_250])
df_time = df_time[df_time["ncores"] < 8]
df_time["cluster_size_cat"] = df_time["cluster_size"].astype("string")


# In[81]:


for i in enumerate(df_time["iteration"]):
    print(i)


# In[58]:


df_250


# In[59]:


df_100


# In[60]:


df_100


# In[55]:


df_time


# In[94]:


times_mean = df_time.groupby(["cluster_size", "ncores", "iteration"])


# In[93]:


for i in enumerate(times_mean):
    print(i)


# In[100]:


df_dict = {
    i: group for i, group in df_time.groupby(["cluster_size", "ncores", "iteration"])
}


# In[101]:


df_dict


# In[117]:


df_speed = pd.DataFrame()
df_list = []
for n_words in [100, 250]:
    for iteration in range(1, 11):
        t1 = df_dict[(n_words, 1, iteration)]["time"].values
        for ncores in range(1, 8):
            speedup = t1 / df_dict[(n_words, ncores, iteration)]["time"].values
            df_ = pd.DataFrame(
                dict(
                    n_words=n_words, ncores=ncores, iteration=iteration, speedup=speedup
                )
            )
            df_list.append(df_)


# In[127]:


df_speed = pd.concat(df_list)
df_speed["n_words_cat"] = df_speed["n_words"].astype("string")


# In[146]:


ax = sns.lineplot(
    data=df_speed[df_speed["iteration"] != 1],
    x="ncores",
    y="speedup",
    hue="n_words_cat",
)
ax.set_aspect("equal")
plt.xlabel("Number of cores")
plt.ylabel("Speedup")
plt.legend(title="Vocabulary size", loc="upper left")
plt.ylim(1, 7)
plt.xlim(1, 7)
ax.plot(
    [0, 1],
    [0, 1],
    transform=ax.transAxes,
    ls="dashed",
    color="lightgray",
    label="Perfect Speedup",
)
plt.savefig("figures/speedup.pdf", **save_args)


# In[122]:


df_speed


# In[ ]:
