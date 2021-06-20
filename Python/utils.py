

import pandas as pd
import numpy as np
import seaborn as sns
import altair as alt
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def limpieza(df, cols):

    for element in cols:
        df[element] = df[element].str.replace(',', '.')
        df[element] = pd.to_numeric(df[element], errors='coerce')
    return df
    

def rellena_nulos_provincia(df, cols_max, cols_min, cols_mean):
    
    # Gropued by provincia and fecha
    df_mean = df.groupby(['provincia', 'fecha', 'Holiday', 'weekday'], as_index=False)[cols_mean].mean()
    df_max = df.groupby(['provincia', 'fecha', 'Holiday', 'weekday'], as_index=False)[cols_max].max()
    df_min = df.groupby(['provincia', 'fecha', 'Holiday', 'weekday'], as_index=False)[cols_min].min()
    # Union of the 3 datasets by provincia and fecha
    df_group = pd.merge(df_mean, df_max, how='inner', on=['provincia', 'fecha', 'Holiday', 'weekday'])
    df_all = pd.merge(df_min, df_group, how='inner', on=['provincia', 'fecha', 'Holiday', 'weekday'])

    return df_all


def sns_generacion(df, tech, systems, fecini_zoom, fecfin_zoom):

  f = plt.figure(figsize=(15, 32))
  gs = f.add_gridspec(len(systems), 1)
  sns.set_style("ticks")
  sns.set_palette("Set2")
  
  for i, sys in enumerate(systems):

    ax = f.add_subplot(gs[i, 0])
    ax.set_title('Generation evolution for '+sys+' system', fontsize=16)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Generation (Mwh', fontsize=12)
    
    filter = (df['Tecnologia'].isin(tech)) & (df['system'] == sys)
    lnplot = sns.lineplot(data=df[filter], x='fecha', y='Generacion_Mwh', ax=ax, legend='full')

    filter_covid = filter & (df['fecha'] >= fecini_zoom) & (df['fecha'] <= fecfin_zoom)
    sns.lineplot(data=df[filter_covid], x='fecha', y='Generacion_Mwh', ax=ax)

    x_ticks = list(range(0, len(lnplot.get_xticklabels()), 365))
    x_ticks.extend([1519, 1610])
    plt.xticks(x_ticks, ['2016', '2017', '2018', '2019', '2020', '2021', fecini_zoom, fecfin_zoom])
    plt.tick_params('x', labelrotation=-45)
    ax.set_xlim(0)
    if sys in ['canarias', 'baleares']:
      ax.set_ylim(5000)
    elif sys == 'peninsular':
      ax.set_ylim(300000)
    else:
      ax.set_ylim(250)
        
    sns.despine()
    sns.set_palette("Set1")
  return None


def target_preprocesing(df, targets_precentage, systems_names):

    for target in targets_precentage:
      df[target] = (df[target]*df['Generacion_Mwh'])

    systems_names.append('fecha')

    df_group = df.groupby(systems_names, as_index=False).sum()

    for target in targets_precentage:
      df_group[target] = (df_group[target]/df_group['Generacion_Mwh'])
    
    return df_group
    

def date_transform(df):

  df['year'] = np.log(df['year'])
  df['day'] = np.cos(((2*np.pi)/31)*df['day'])
  df['month'] = np.cos(((2*np.pi)/12)*df['month'])
  df['weekday'] = np.cos(((2*np.pi)/7)*df['weekday'])

  return df
  

def train_test_val_split(df, features, targets, percentaje_test, percentaje_val):
  # Para no predecir con datos de futuro separo los datos en train y test por fecha
  
  total = len(df.index)
  row_test = np.round(total-(total*(percentaje_test+percentaje_val)), 0).astype(np.int)
  row_val = np.round(total-(total*percentaje_val), 0).astype(np.int)
  
  train = df.iloc[:row_test]
  test = df.iloc[row_test:row_val]
  val = df.iloc[row_val:]

  X_train = train[features]
  y_train = train[targets]

  X_test = test[features]
  y_test = test[targets]
  
  X_validation = val[features]
  y_validacion = val[targets]

  return X_train, X_test, y_train, y_test, X_validation, y_validacion
  
  
def evaluation_function(y_real, y_pred, model):
  '''Calculate de value por each metric for y_real and y_pred then plot it por each model'''
  results = {}
  results['Model_name'] = [model]
  result_mae = mean_absolute_error(y_real, y_pred)
  results['MAE'] = [result_mae]
  result_rmse = mean_squared_error(y_real, y_pred, squared=False)
  results['RMSE'] = [result_rmse]
  results['R2'] = [r2_score(y_real, y_pred)]

  return pd.DataFrame.from_dict(data=results)


def plot_metrics(list_reg):

  df = list_reg[0]
  
  for element in list_reg[1:]:
    df = df.append(element)
    
  fig, ax =plt.subplots(3, 1, sharey=True)
  fig.set_size_inches(12, 12)
  fig.suptitle('Comparativa de metricas entre Modelos', fontsize=12)
 
  #MAE
  sns.barplot(y=df['Model_name'], x=df['MAE'], ax=ax[0])
  ax[0].set_title("MAE Compare", fontsize=10)
  
  #RMSE
  sns.barplot(y=df['Model_name'], x=df['RMSE'], ax=ax[1])
  ax[1].set_title("RMSE Compare", fontsize=10)

  #R2
  sns.barplot(y=df['Model_name'], x=df['R2'], ax=ax[2])
  ax[2].set_title("R2 Compare", fontsize=10)

  return None
  
def plot_real_vs_pred(system, target, X_test, y_test, reg_ln, reg_KN, reg_DT, reg_XGB, reg_LGBM):
  subplt = len(target) * 4
  size = len(target) * 20
  f, ax = plt.subplots(subplt, 1)
  f.set_size_inches(18, size)

  y_real = pd.DataFrame(data=y_test[y_test[system] == 1])[target]
  y_real['Model'] = 'Real'
  y_real.reset_index(inplace=True)

  y_pred_ln = pd.DataFrame(reg_ln.predict(X_test[X_test[system] == 1]), columns=target)
  y_pred_ln['Model'] = 'Linear Regresor (Base model)'

  y_pred_KN = pd.DataFrame(reg_KN.predict(X_test[X_test[system] == 1]), columns=target)
  y_pred_KN['Model'] = 'KNeighbors'

  y_pred_DT = pd.DataFrame(reg_DT.predict(X_test[X_test[system] == 1]), columns=target)
  y_pred_DT['Model'] = 'Decision Tree'

  y_pred_XGB = pd.DataFrame(reg_XGB.predict(X_test[X_test[system] == 1]), columns=target)
  y_pred_XGB['Model'] = 'XGBoost'

  y_pred_LGBM = pd.DataFrame(reg_LGBM.predict(X_test[X_test[system] == 1]), columns=target)
  y_pred_LGBM['Model'] = 'LightGBM'

  result = pd.concat([y_real, y_pred_ln, y_pred_KN, y_pred_DT, y_pred_XGB, y_pred_LGBM])

  models_filter0 = result['Model'].isin(['Real', 'Linear Regresor (Base model)', 'KNeighbors'])
  models_filter1 = result['Model'].isin(['Real', 'Linear Regresor (Base model)', 'Decision Tree'])
  models_filter2 = result['Model'].isin(['Real', 'Linear Regresor (Base model)', 'XGBoost'])
  models_filter3 = result['Model'].isin(['Real', 'Linear Regresor (Base model)', 'LightGBM'])

  sns.set_style("ticks")

  for i, element in enumerate(target):

    if i > 0:
      i = i * 4
    sns.lineplot(data=result[models_filter0], y=element, x=result[models_filter0].index, hue='Model', ax=ax[i])
    sns.lineplot(data=result[models_filter1], y=element, x=result[models_filter1].index, hue='Model', ax=ax[i + 1])
    sns.lineplot(data=result[models_filter2], y=element, x=result[models_filter2].index, hue='Model', ax=ax[i + 2])
    sns.lineplot(data=result[models_filter3], y=element, x=result[models_filter3].index, hue='Model', ax=ax[i + 3])

  sns.despine()

  return None


def chart_altair(df, system_ini='peninsular'):

    x_labels = ['2016-01-01', '2016-02-01', '2016-03-01', '2016-04-01', '2016-05-01', '2016-06-01',
                '2016-07-01', '2016-08-01', '2016-09-01', '2016-10-01', '2016-11-01', '2016-12-01', '2016-12-31',
                '2017-01-01', '2017-02-01', '2017-03-01', '2017-04-01', '2017-05-01', '2017-06-01',
                '2017-07-01', '2017-08-01', '2017-09-01', '2017-10-01', '2017-11-01', '2017-12-01', '2017-12-31',
                '2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01',
                '2018-07-01', '2018-08-01', '2018-09-01', '2018-10-01', '2018-11-01', '2018-12-01', '2018-12-31',
                '2019-01-01', '2019-02-01', '2019-03-01', '2019-04-01', '2019-05-01', '2019-06-01',
                '2019-07-01', '2019-08-01', '2019-09-01', '2019-10-01', '2019-11-01', '2019-12-01', '2019-12-31',
                '2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01', '2020-06-01',
                '2020-07-01', '2020-08-01', '2020-09-01', '2020-10-01', '2020-11-01', '2020-12-01', '2020-12-31',
                '2021-01-01', '2021-02-01', '2021-03-01', '2021-04-01', '2021-05-01', '2021-06-01',
                '2021-07-01', '2021-08-01', '2021-09-01', '2021-10-01', '2021-11-01', '2021-12-01', '2021-12-31']

    domain = ['Generación total', 'Renovable', 'Solar fotovoltaica', 'Eólica']
    range_ = ['#85C1E9', '#239B56', '#D35400', '#F7DC6F']

    select_box_sys = alt.binding_select(options=list(df['system'].unique()))

    selection_sys = alt.selection_single(name='REE',
                                         fields=['system'],
                                         bind=select_box_sys,
                                         init={'system': system_ini})

    select_radio_year = alt.binding_radio(options=list(df['year'].unique()))

    selection_year = alt.selection_single(name='Choose',
                                          fields=['year'],
                                          bind=select_radio_year,
                                          init={'year': max(df['year'])})

    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['fecha'], empty='none')

    selectors = alt.Chart(df).mark_point().encode(
        alt.X('fecha'),
        opacity=alt.value(0)
    ).add_selection(
        nearest
    ).transform_filter(
        selection_sys
    ).transform_filter(
        selection_year
    )

    bar = alt.Chart(df[df['Renov_norenov'] == 'Generación total']).mark_area(color='#85C1E9').encode(
        alt.X('fecha', axis=alt.Axis(values=x_labels, labelAngle=0)),
        alt.Y('Generacion_Mwh:Q')

    ).add_selection(
        selection_sys, selection_year
    ).transform_filter(
        selection_sys
    ).transform_filter(
        selection_year
    ).properties(
        width=1400,
        height=450
    )


    bar_renov = alt.Chart(df[df['Tecnologia'] == 'Renovable']).mark_area().encode(
        alt.X('fecha'),
        alt.Y('Generacion_Mwh:Q'),
        color=alt.Color('Tecnologia', scale=alt.Scale(domain=domain, range=range_))
    ).transform_filter(
        selection_sys
    ).transform_filter(
        selection_year
    )

    text_renov = bar_renov.mark_text(align='left', dx=3, dy=-20, color='#212F3C').encode(
        text=alt.condition(nearest, 'Generacion_Mwh', alt.value(' '))
    )

    rules = alt.Chart(df).mark_rule(color='gray').encode(
        x='fecha',
    ).transform_filter(
        nearest
    )

    bar_solar = alt.Chart(df[df['Tecnologia'] == 'Solar fotovoltaica']).mark_area(opacity=.8, color='#D35400').encode(
        alt.X('fecha'),
        alt.Y('Generacion_Mwh:Q')
    ).transform_filter(
        selection_sys
    ).transform_filter(
        selection_year
    )

    text_solar = bar_solar.mark_text(align='left', dx=5, dy=-5, color='#212F3C').encode(
        text=alt.condition(nearest, 'Generacion_Mwh', alt.value(' '))
    )

    bar_eolica = alt.Chart(df[df['Tecnologia'] == 'Eólica']).mark_area(color='#F7DC6F').encode(
        alt.X('fecha'),
        alt.Y('Generacion_Mwh:Q')
    ).transform_filter(
        selection_sys
    ).transform_filter(
        selection_year
    )

    text_eolica = bar_eolica.mark_text(align='left', dx=5, dy=-5, color='#212F3C').encode(
        text=alt.condition(nearest, 'Generacion_Mwh', alt.value(' '))
    )

    return alt.layer(bar, bar_renov, bar_eolica, bar_solar, selectors, rules, text_renov, text_eolica, text_solar
                    ).configure_axis(labelFontSize=13,titleFontSize=14
                    ).configure_text(fill='#212F3C', fontSize=13
                    ).configure_legend(labelFontSize=14).interactive()

