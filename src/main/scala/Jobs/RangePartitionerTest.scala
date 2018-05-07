package Jobs

import Jobs.ExtractGitHubData.{connectionString, jdbcProperties}
import Jobs.Extractor.CommitRecord.extractCommit
import org.apache.spark.sql.{SaveMode, SparkSession}
import org.apache.spark.{SparkConf, SparkContext}

class RangePartitionerTest {
  def main(args: Array[String]): Unit = {
    // Extract the arguments
    val dataDirectory: String = args match {
      case Array(dir) => dir
      case _ => throw new Error("Invalid arguments passed")
    }
    
    // setup the spark context
    val conf = new SparkConf().setAppName("Parsing GitHub Commits")
    val sc = new SparkContext(conf)
    
    // SparkSQL
    val spark = SparkSession.builder().getOrCreate()
    import spark.implicits._
    
    // Read text files into spark RDD, map to objects and convert to DF
    val commitsDf = spark.read.textFile(s"$dataDirectory/commits.json")
      .flatMap{s => extractCommit(s)}
    //      .groupBy("commit_date", "language_name", "import_name")
    //      .sum("usage_count")
    //      .withColumnRenamed("sum(usage_count)", "usage_count")
    
    // Write the DataFrame to DB
    commitsDf.write.mode(SaveMode.Append).jdbc(connectionString, "github_commits", jdbcProperties)
  }
}
