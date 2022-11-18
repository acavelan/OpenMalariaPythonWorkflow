import math, os, sys, subprocess, torch, shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
from measures import mm, mmi

rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
rc('text', usetex=True)

def prevalence2to10_to_incidence(df, measures, age_groups_on_plot, age_groups, title, y_lim, filename):
    modes = df['mode'].unique()
    modelNames = df['modelName'].unique()

    nx = len(modelNames); ny = len(modes); f = 1; firstPlot = True
    fig = plt.figure(figsize=(12,8))
    for mode in modes:
        for modelName in modelNames:
            g = df[(df["modelName"] == modelName) & (df["mode"] == mode)]

            # compute prevalence 2 to 10
            age2to10 = (age_groups[g.ageGroup-1] >= 2) & (age_groups[g.ageGroup-1] <= 10)
            nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['eir', 'ageGroup', 'seed']).value.sum()
            nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['eir', 'ageGroup', 'seed']).value.sum()
            prevalence2to10 = (nPatent2to10 / nHost2to10).groupby('eir').mean() * 100

            # for each age group, plot x = prevalence 2_to_10, y = incidences
            ax = fig.add_subplot(ny,nx,f); f += 1;
            for i in range(0, len(age_groups_on_plot)):
                ages = age_groups_on_plot[i]
                ageCond = (age_groups[g.ageGroup-1] >= ages[0]) & (age_groups[g.ageGroup-1] <= ages[1])

                # group by age groups (sum)
                nCases = 0
                for m in measures:
                    nCases += g[(g.measure == mmi[m]) & ageCond].groupby(['eir', 'seed']).value.sum()

                nHost = g[(g.measure == mmi['nHost']) & ageCond].groupby(['eir', 'seed']).value.sum()

                incidence = nCases / (nHost / 12)

                # plot mean, min and max of seeds
                ax.plot(prevalence2to10, incidence.groupby('eir').mean(), marker='o', label=f"{ages[0]}-{ages[1]}" if firstPlot else "")
                ax.fill_between(prevalence2to10, incidence.groupby('eir').min(), incidence.groupby('eir').max(), alpha=0.3)
                
            ax.set_ylim(y_lim)
            ax.set_xlim(0, 80)
            ax.set_xticks([0, 20, 40, 60, 80, 90])
            ax.set_xticklabels([str(i)+'%' for i in [0, 20, 40, 60, 80, 90]])
            if firstPlot: ax.legend(loc="upper left", title="age groups",title_fontproperties={"weight": "bold"})
            firstPlot = False

    # Decorations
    for i in range(0, len(modelNames)):
        coord = (i+1)/len(modelNames)-1.0/len(modelNames)/2
        fig.text(coord, 0.98, modelNames[i], ha='center', va='center', fontsize=16)
        
    fig.text(0.98, 0.75, 'Perennial', ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.98, 0.25, 'Seasonal', ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.5, 0.02, 'PfPR_{2-10}\%', ha='center', va='center', fontsize=16)
    fig.text(0.02, 0.5, title, ha='center', va='center', rotation='vertical', fontsize=16)
    plt.tight_layout(rect=[0.025, 0.025, 0.985, 0.985])
    fig.savefig(filename)

def age_incidence(df, mode, measures, title, prev_categories, y_lim, age_groups, filename):
    modelNames = df['modelName'].unique()

    nx = len(modelNames); ny = 4; f = 0; firstPlot = True
    fig = plt.figure(figsize=(8,8))

    gs = fig.add_gridspec(ny, nx, hspace=0, wspace=0)
    axes = gs.subplots(sharex='col', sharey='row').flatten()

    for i in range(len(prev_categories)):
        for modelName in modelNames:
            ax = axes[f]; f += 1
                    
            g = df[(df["modelName"] == modelName) & (df["mode"] == mode)]

            # compute prevalence 2 to 10
            age2to10 = (age_groups[g.ageGroup-1] >= 2) & (age_groups[g.ageGroup-1] <= 10)
            nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['eir','seed']).value.sum()
            nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['eir','seed']).value.sum()
            prevalence2to10 = ((nPatent2to10 / nHost2to10).groupby('eir').mean() * 100).reset_index()
            
            # group by age groups (sum)
            nCases = 0
            for m in measures:
                nCases += g[(g.measure == mmi[m]) & (age_groups[g.ageGroup-1] <= 20)].groupby(['eir', 'ageGroup', 'seed']).value.sum()
            
            nCases = nCases.groupby(['eir', 'ageGroup', 'seed']).sum().reset_index()
            nHost = g[(g.measure == mmi['nHost']) & (age_groups[g.ageGroup-1] <= 20)].groupby(['eir', 'ageGroup', 'seed']).value.sum().reset_index()
            
            # add prevalence2to10 to ncases and nHost to filter later
            nCases = nCases.merge(prevalence2to10, on="eir")
            nHost = nHost.merge(prevalence2to10, on="eir")
            
            # select nCases and nHost for the given prevalence category 
            prev_cat = prev_categories[i]
            nCases = nCases[(nCases.value_y >= prev_cat[0]) & (nCases.value_y <= prev_cat[1])].groupby(['eir', 'ageGroup', 'seed']).sum()
            nHost = nHost[(nHost.value_y >= prev_cat[0]) & (nHost.value_y <= prev_cat[1])].groupby(['eir', 'ageGroup', 'seed']).sum()
            incidence = (nCases / (nHost / 12)).groupby(['ageGroup']).value_x
            
            if incidence.mean().empty:
                continue
            
            ages = age_groups[incidence.mean().index - 1]

            # plot mean, min and max of seeds and EIR
            ax.plot(ages, incidence.mean(), marker='o', label=f"{modelName}")
            ax.fill_between(ages, incidence.min(), incidence.max(), alpha=0.3)

            ax.set_ylim(y_lim)
            ax.set_xticks([0.0, 5.0, 10.0, 15,0, 20.0])
            ax.set_xticklabels([0.0, 5.0, 10.0, 15,0, 20.0])
    
        for i in range(0, len(modelNames)):
            coord = (i+1)/len(modelNames)-1.0/len(modelNames)/2
            fig.text(coord, 0.98, modelNames[i], ha='center', va='center', fontsize=16)
        
        for i in range(0, len(prev_categories)):
            prev_cat = prev_categories[i]
            coord = (i+1)/len(prev_categories)-1.0/len(prev_categories)/2
            fig.text(0.98, 1-coord, f'PfPR_{prev_cat[0]}-{prev_cat[1]}\%', ha='center', va='center', rotation=-90, fontsize=16)
        
        fig.text(0.02, 0.5, title, ha='center', va='center', rotation='vertical', fontsize=16)
        fig.text(0.5, 0.02, 'age', ha='center', va='center', fontsize=16)
        plt.tight_layout(rect=[0.025, 0.025, 0.975, 0.985])
        fig.savefig(filename)

def eir_to_prevalence2to10(df, mode, age_groups, filename):
    modelNames = df['modelName'].unique()

    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(1,1,1)

    for modelName in modelNames:
                
        g = df[(df["modelName"] == modelName) & (df["mode"] == mode)]

        # compute prevalence 2 to 10
        age2to10 = (age_groups[g.ageGroup-1] >= 2) & (age_groups[g.ageGroup-1] <= 10)
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['eir','seed']).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['eir','seed']).value.sum()
        prevalence2to10 = (nPatent2to10 / nHost2to10).groupby('eir')
        
        simulatedEIR = g[(g.measure == mmi['SimulatedEIR'])].groupby(['eir']).value.mean() * 6
        
        if prevalence2to10.mean().empty:
            continue

        # plot mean, min and max of seeds
        ax.plot(simulatedEIR, prevalence2to10.mean() * 100, marker='o', label=f"{modelName} - {mode}")
        ax.fill_between(simulatedEIR, prevalence2to10.min() * 100, prevalence2to10.max() * 100, alpha=0.3)

    ax.set_xscale('symlog')
    # ax.set_xticks([0, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000])
    # ax.set_xticklabels([0, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000])
    ax.set_yticks([0, 10, 20, 30, 40, 50, 60, 70, 80])
    ax.set_yticklabels([0, 10, 20, 30, 40, 50, 60, 70, 80])

    ax.legend(loc="lower right")
    ax.set_xlabel('simulated annual EIR')
    ax.set_ylabel('PfPR_{2-10}\%')
    plt.tight_layout()
    fig.savefig(filename)
