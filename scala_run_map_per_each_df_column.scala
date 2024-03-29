

//Spark local
//spark2-shell --queue general --conf spark.ui.port=4060 --driver-class-path /etc/spark2/conf:/etc/hive/conf --master=local 

val hdfsTablesBaseLoc = "file:///home/km/merchant"
val inputFileHDFSPath = hdfsTablesBaseLoc+"/data.csv"

val zip4DF=spark.read.
 options(Map("delimiter"->",", "header"->"True")).
 csv(inputFileHDFSPath) //. show(false)

zip4DF.columns.map( x => {
 try{
  (x, spark.sql(s"SELECT count(1) FROM table WHERE ${x}='' OR ${x} IS NULL").map(_.getLong(0).toString).collect.mkString(",") )
 }catch{
      case ex: Exception => { (x, "") }
 }
}).toSeq.toDF("column","count")

