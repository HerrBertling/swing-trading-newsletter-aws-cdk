import * as cdk from "@aws-cdk/core"
import * as dynamodb from "@aws-cdk/aws-dynamodb"
import * as lambdaPy from "@aws-cdk/aws-lambda-python"
import {Runtime} from "@aws-cdk/aws-lambda"
import * as sfn from "@aws-cdk/aws-stepfunctions"
import * as tasks from "@aws-cdk/aws-stepfunctions-tasks"
import * as iam from "@aws-cdk/aws-iam"
import * as sqs from "@aws-cdk/aws-sqs"
import {SqsEventSource} from "@aws-cdk/aws-lambda-event-sources"
import {Rule, Schedule} from "@aws-cdk/aws-events"
import {SfnStateMachine, LambdaFunction} from "@aws-cdk/aws-events-targets"
import {Duration} from "@aws-cdk/core"

const LAMBDA_FOLDER = "lib/lambda"
const DEFAULT_MEMORY = 1280
const DEFAULT_TIMEOUT = cdk.Duration.minutes(5)

export class TrueffelCdkStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const stockScreenTable = new dynamodb.Table(this, "StocksTable", {
      partitionKey: {name: "symbol", type: dynamodb.AttributeType.STRING},
      sortKey: {name: "date", type: dynamodb.AttributeType.STRING},
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    })

    const marketCheckTable = new dynamodb.Table(this, "MarketCheckTable", {
      partitionKey: {name: "date", type: dynamodb.AttributeType.STRING},
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    })

    const defaultLambdaSettings = {
      memorySize: DEFAULT_MEMORY,
      timeout: DEFAULT_TIMEOUT,
    }

    const defaultsWithStockDatabase = {
      ...defaultLambdaSettings,
      environment: {
        DATABASE: stockScreenTable.tableName,
      },
    }

    const marketCheck = new lambdaPy.PythonFunction(this, "MarketCheck", {
      entry: `${LAMBDA_FOLDER}/marketCheck`,
      ...defaultLambdaSettings,
      environment: {
        DATABASE: marketCheckTable.tableName,
      },
    })

    const healthCheck = new lambdaPy.PythonFunction(this, "HealthCheck", {
      entry: `${LAMBDA_FOLDER}/stock_healthcheck`,
      ...defaultsWithStockDatabase,
    })

    const dailyEmail = new lambdaPy.PythonFunction(this, "DailyEmail", {
      entry: `${LAMBDA_FOLDER}/dailyEmail`,
      ...defaultLambdaSettings,
      environment: {
        DATABASE: stockScreenTable.tableName,
        MARKETCHECK: marketCheckTable.tableName,
      },
    })

    const aemap = new lambdaPy.PythonFunction(this, "AEMAp", {
      entry: `${LAMBDA_FOLDER}/aemap`,
      ...defaultsWithStockDatabase,
    })

    const forceIndex = new lambdaPy.PythonFunction(this, "ForceIndex", {
      entry: `${LAMBDA_FOLDER}/force_index`,
      ...defaultsWithStockDatabase,
    })

    const impulseSystem = new lambdaPy.PythonFunction(this, "ImpulseSystem", {
      entry: `${LAMBDA_FOLDER}/impulse_system`,
      ...defaultsWithStockDatabase,
    })

    const allowSesMailsInLambda = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: ["*"],
      actions: ["ses:SendEmail"],
    })

    stockScreenTable.grantReadWriteData(impulseSystem)
    stockScreenTable.grantReadWriteData(forceIndex)
    stockScreenTable.grantReadWriteData(aemap)

    stockScreenTable.grantReadData(dailyEmail)
    marketCheckTable.grantReadData(dailyEmail)

    marketCheckTable.grantReadWriteData(marketCheck)

    dailyEmail.addToRolePolicy(allowSesMailsInLambda)

    const stockHealthCheck = new tasks.LambdaInvoke(
      this,
      "Stock Health Check",
      {
        lambdaFunction: healthCheck,
        resultPath: "$.health",
        payloadResponseOnly: true,
      }
    )

    const weeklyIndicator = new tasks.LambdaInvoke(this, "Weekly Indicator", {
      lambdaFunction: impulseSystem,
      inputPath: "$",
      payloadResponseOnly: true,
      resultPath: "$",
    })

    const dailyIndicator = new tasks.LambdaInvoke(this, "Daily Indicator", {
      lambdaFunction: forceIndex,
      inputPath: "$",
      payloadResponseOnly: true,
      resultPath: "$.daily",
    })

    const entryIndicator = new tasks.LambdaInvoke(this, "Entry Indicator", {
      lambdaFunction: aemap,
      inputPath: "$",
    })

    const leFin = new sfn.Succeed(this, "Over and out!")

    const hasPassedHealthCheck = new sfn.Choice(this, "Is stock healthy?")

    const stockIsHealthy = sfn.Condition.stringEquals(
      "$.health.shouldProceed",
      "true"
    )

    const proceedToDaily = new sfn.Choice(this, "Proceed to daily?")

    const shouldProceedToDaily = sfn.Condition.not(
      sfn.Condition.stringEquals("$.weekly.result", "red")
    )

    const proceedToEntry = new sfn.Choice(this, "Proceed to entry?")

    const shouldProceedToEntry = sfn.Condition.stringEquals(
      "$.daily.result",
      "long"
    )

    const chain = sfn.Chain.start(stockHealthCheck).next(
      hasPassedHealthCheck
        .when(
          stockIsHealthy,
          weeklyIndicator.next(
            proceedToDaily
              .when(
                shouldProceedToDaily,
                dailyIndicator.next(
                  proceedToEntry
                    .when(shouldProceedToEntry, entryIndicator.next(leFin))
                    .otherwise(leFin)
                )
              )
              .otherwise(leFin)
          )
        )
        .otherwise(leFin)
    )

    const tripleScreenStateMachine = new sfn.StateMachine(
      this,
      "TripleScreenSteps",
      {
        definition: chain,
        timeout: cdk.Duration.minutes(15),
      }
    )

    const sfnQueue = new sqs.Queue(this, "StepFunctionQueue", {
      queueName: "SFNQueue",
      visibilityTimeout: Duration.seconds(600),
    })

    const fanOutStockSymbols = new lambdaPy.PythonFunction(
      this,
      "FanOutStockSymbols",
      {
        entry: `${LAMBDA_FOLDER}/fanOutStockSymbols`,
        ...defaultLambdaSettings,
        environment: {
          QUEUENAME: sfnQueue.queueName,
        },
      }
    )

    const historicalDataFanOut = new lambdaPy.PythonFunction(
      this,
      "HistoricalDataFanOut",
      {
        ...defaultLambdaSettings,
        entry: `${LAMBDA_FOLDER}/historicalDataFanOut`,
        timeout: Duration.minutes(15),
        environment: {
          QUEUENAME: sfnQueue.queueName,
        },
      }
    )

    const triggerStepFunction = new lambdaPy.PythonFunction(
      this,
      "TriggerStepFunction",
      {
        ...defaultLambdaSettings,
        entry: `${LAMBDA_FOLDER}/triggerStepFunction`,
        environment: {
          STATEMACHINE: tripleScreenStateMachine.stateMachineArn,
        },
      }
    )
    tripleScreenStateMachine.grantStartExecution(triggerStepFunction)

    const triggerStepFunctionStateMachine = new SfnStateMachine(
      tripleScreenStateMachine
    )

    const eventSource = triggerStepFunction.addEventSource(
      new SqsEventSource(sfnQueue)
    )

    sfnQueue.grantSendMessages(historicalDataFanOut)
    sfnQueue.grantSendMessages(fanOutStockSymbols)
    sfnQueue.grantConsumeMessages(triggerStepFunction)

    const fanOutTargetLambda = new LambdaFunction(fanOutStockSymbols)

    const dailyEmailLambda = new LambdaFunction(dailyEmail)

    const marketCheckLambda = new LambdaFunction(marketCheck)

    new Rule(this, "RegularStockFanOut", {
      schedule: Schedule.cron({minute: "0", hour: "2", weekDay: "MON-FRI"}),
      ruleName: "FanOutStockSymbolsCron",
      targets: [fanOutTargetLambda],
    })

    new Rule(this, "RegularMarketCheck", {
      schedule: Schedule.cron({minute: "0", hour: "3", weekDay: "MON-FRI"}),
      ruleName: "RegularMarketCheckCron",
      targets: [marketCheckLambda],
    })

    new Rule(this, "DailyEmailTrigger", {
      schedule: Schedule.cron({minute: "0", hour: "6", weekDay: "MON-FRI"}),
      ruleName: "SendDailyEmailCron",
      targets: [dailyEmailLambda],
    })

    // HISTORICAL ANALYSIS

    const historicalQueue = new sqs.Queue(this, "HistoricalAnalysisQueue", {
      queueName: "HiAnaQueue",
      visibilityTimeout: Duration.seconds(900),
    })

    const historicalAnalysis = new lambdaPy.PythonFunction(
      this,
      "HistoricalAnalysis",
      {
        ...defaultLambdaSettings,
        entry: `${LAMBDA_FOLDER}/historical_analysis`,
        timeout: Duration.minutes(15),
        environment: {
          DATABASE: stockScreenTable.tableName,
          QUEUENAME: historicalQueue.queueName,
        },
      }
    )
    const historicalAnalysisPerEntry = new lambdaPy.PythonFunction(
      this,
      "HistoricalAnalysisPerEntry",
      {
        ...defaultLambdaSettings,
        entry: `${LAMBDA_FOLDER}/historical_analysis_per_entry`,
        timeout: Duration.minutes(15),
        environment: {
          DATABASE: stockScreenTable.tableName,
        },
      }
    )
    stockScreenTable.grantReadData(historicalAnalysis)
    historicalQueue.grantSendMessages(historicalAnalysis)
    historicalQueue.grantConsumeMessages(historicalAnalysisPerEntry)

    const historicalPerEntryEventSource = historicalAnalysisPerEntry.addEventSource(
      new SqsEventSource(historicalQueue)
    )
  }
}
