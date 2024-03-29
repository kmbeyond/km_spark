
import pyspark.sql.functions as F
from pyspark.sql.types import StringType
data = spark.createDataFrame([('ILLINOIS'), ('North Carolina'), ('XX'), ('NEWYORK')], StringType()).toDF('state')


state_abbr = {'IOWA': 'IA', 'KANSAS': 'KS', 'FLORIDA': 'FL', 'VIRGINIA': 'VA', 'NORTH CAROLINA': 'NC', 'SOUTH DAKOTA': 'SD', 'ALABAMA': 'AL', 'IDAHO': 'ID',
  'DELAWARE': 'DE', 'ALASKA': 'AK', 'CONNECTICUT': 'CT', 'TENNESSEE': 'TN', 'PUERTO RICO': 'PR', 'NEW MEXICO': 'NM', 'MISSISSIPPI': 'MS',
  'COLORADO': 'CO', 'NEW JERSEY': 'NJ', 'UTAH': 'UT', 'MINNESOTA': 'MN', 'VIRGIN ISLANDS': 'VI', 'NEVADA': 'NV',
  'ARIZONA': 'AZ', 'WISCONSIN': 'WI', 'NORTH DAKOTA': 'ND', 'PENNSYLVANIA': 'PA', 'OKLAHOMA': 'OK', 'KENTUCKY': 'KY',
  'RHODE ISLAND': 'RI', 'NEW HAMPSHIRE': 'NH', 'MISSOURI': 'MO', 'MAINE': 'ME', 'VERMONT': 'VT', 'GEORGIA': 'GA',
  'GUAM': 'GU', 'AMERICAN SAMOA': 'AS', 'NEW YORK': 'NY', 'CALIFORNIA': 'CA', 'HAWAII': 'HI', 'ILLINOIS': 'IL', 'NEBRASKA': 'NE',
  'MASSACHUSETTS': 'MA', 'OHIO': 'OH', 'MARYLAND': 'MD', 'MICHIGAN': 'MI', 'WYOMING': 'WY', 'WASHINGTON': 'WA', 'OREGON': 'OR', 'SOUTH CAROLINA': 'SC',
  'INDIANA': 'IN', 'LOUISIANA': 'LA', 'NORTHERN MARIANA ISLANDS': 'MP', 'DISTRICT OF COLUMBIA': 'DC', 'MONTANA': 'MT', 'ARKANSAS': 'AR', 'WEST VIRGINIA': 'WV', 'TEXAS': 'TX'}

br_lst_format_state = spark.sparkContext.broadcast(state_abbr)


#------directly from dict --NOT EASY SOLUTION WITH withColumn()---
#--using na.replace()
df2 = data.withColumn('state', F.upper(F.col('state')) ).na.replace(b_lst_format_state.value, subset=['state'])
+-------+---+
|  state|zip|
+-------+---+
|     IL|123|
|     NC|123|
|     XX|123|
|NEWYORK|123|
+-------+---+
states_list = list( set(state_abbr.values()) )
br_states_list = spark.sparkContext.broadcast(states_list)

df2.withColumn('state', F.when(F.col('state').isin(br_states_list.value), F.col('state')).otherwise(F.lit(None)) ).show(5)

--NOT WORKING---
data.withColumn('state_formatted', F.lit(b_lst_format_state.value.get(F.upper(F.col("state")), 'INVALID')) ).show(5)
data.withColumn('state_formatted', F.lit(b_lst_format_state.value.get(F.decode(F.upper(F.col('state')), 'UTF-8'), 'INVALID')) ).show(5)

--convert between RDD & DF
data.rdd.map(lambda x: Row(b_lst_format_state.value.get(x[0].upper(), 'INVALID')) ).toDF(['state']).show(5)

data = spark.createDataFrame([('ILLINOIS','123'), ('North Carolina','123'), ('XX','123'), ('NEWYORK','123'), (None,None)]).toDF('state','zip')
data.na.replace(b_lst_format_state.value, 1).show()
data.rdd.map(lambda x: Row(b_lst_format_state.value.get(x[0].upper()),x[1]) ).toDF(['state','zip']).show(5)



#------using create_map & chain
from itertools import chain
mapping_expr = F.create_map([F.lit(x) for x in chain(*b_lst_format_state.value.items())])

data.withColumn('state_formatted', mapping_expr.getItem(F.upper(F.col('state'))) ).show(5)
+--------------+---------------+
|         state|state_formatted|
+--------------+---------------+
|      ILLINOIS|             IL|
|North Carolina|             NC|
|            XX|           null|
|       NEWYORK|           null|
+--------------+---------------+


#------using udf
#one-liner udf
formatSateUDF = F.udf(lambda x: b_lst_format_state.value.get(x, 'INVALID') )

#expanded udf
def formatState(s):
 #b_lst_format_state.value = b_lst_format_state.value
 s = b_lst_format_state.value.get(s, 'INVALID')
 return s

formatSateUDF = F.udf(lambda x: formatState(x))

data.withColumn('state_formatted', formatSateUDF(F.upper(F.col("state"))) ).show(5)
####data.withColumn('state_formatted', F.when(F.length(F.col('state'))==2, F.upper(F.col("state"))).when(F.length(F.col('state'))>2, formatSateUDF(F.upper(F.col("state"))) ).otherwise(F.lit('')) ).show(5)

+--------------+---------------+
|         state|state_formatted|
+--------------+---------------+
|      ILLINOIS|             IL|
|North Carolina|             NC|
|            XX|        INVALID|
|       NEWYORK|        INVALID|
+--------------+---------------+

#----using udf with passing dict into udf
from pyspark.sql.types import StringType
def getStateAbbr(state_lookup):
  return F.udf(lambda col: state_lookup.get(col.upper(),'INVALID'), StringType())

--OR--
def getStateAbbr2(mapping_list):
    def translate_(col):
        return mapping_list.get(col.upper(), 'INVALID')
    return F.udf(translate_, StringType())

data.withColumn("state_formatted", getStateAbbr(b_lst_format_state.value)('state') ).show(5)

