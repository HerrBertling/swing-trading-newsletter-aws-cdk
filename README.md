# swing-trading-newsletter-aws-cdk

## 🏎 TL;DR

This is an AWS CDK setup to create a newsletter that gives you a daily list of pre-screened S&P 500 stocks, a possible entry price for each and the tiny hope that you're able to sell them a few days later with a bit of profit.

## 💡 The idea

I built this newsletter to have a daily check on various stocks – in this case, the S&P 500 stocks. It produces a list of stocks you could invest in on that given day.

This newsletter only targets stocks to go long in. It does not offer short trading advice. It only tells you which stocks you _could_ buy to which entry price based on a Triple Screen Trading System. 

## 📝 "Writing" the newsletter

Every night (CET timezone), all S&P 500 stocks are checked via a Triple Screen Trading System. In the morning, the results of the nightly run are evaluated. Every stock with a possible entry price is thrown into an email that is sent out.

Besides that, the email includes a small market check with some common indicators.

### ❓ What is the Triple Screen Trading System?

The Triple Screen Trading System checks three timeframes. Per timeframe, a stock indicator is applied. If the indicator gives the correct signal, you progress to the next timeframe.

You can compare it to going surfing: First, you check the tide. Is it okay? Good, off to the beach! At the beach, you check the waves. Are they any good? Great, jump into the water to catch waves! The final check is for finding a good entry into the (market) waves.

### 🤓 Which indicators are used?

Every stock below an average trading volume of one million traded stocks per day across the last five days is skipped. This ensures that you end up with actively traded stocks.

For the weekly check, the [Impulse System](https://school.stockcharts.com/doku.php?id=chart_analysis:elder_impulse_system) is used. If it is not red, it proceeds to the daily check.

The daily check is done via the [Force Index](https://www.investopedia.com/terms/f/force-index.asp) (with a short EMA of two days). If it crossed the line from a positive to a negative value in the last two days, the check proceeds to the possible entry calculation.

The entry check then calculates the average exponential moving average (EMA) penetration for the last 20 days of trading. This needs a longer explanation, feel free to skip this. It takes the prices and the exponential moving average and collects all "dips" of the price below the EMA as a difference. Then you take the average of these differences and substract it from the last closing price. That's your possible entry price.

### 🕵️‍♂️ Where is the stock data coming from?

The newsletter uses the (unofficial 😏) Yahoo Finance API which provides Open/High/Low/Close/Volume data on all of the used stocks.

### 🤔 Does this work?

No idea, go find out 😅

## ⚠️ Disclaimer

Of course, this newsletter is not giving you financial or trading advice. Before you buy any stock, you should thoroughly check them and make your own investment decisions. This email newsletter serves simply as a little help to find eventually interesting stocks. Have fun.

## Technical setup

You can use this repo to spin up an AWS setup that takes care of everything described above. It has some step functions, quite some lambdas, some triggers and a database setup for data collection.

Check out the `lib/trueffel-cdk-stack.ts` file, it has the whole CDK stack.

### Setup / Installation

Clone this repo, run `yarn` and you should be good to go with the commands described below.

I never setup a local dev environment. My approach honestly was: "Let's deploy this and send a test email to see if it works" plus reading a lot of CloudWatch outputs 😄

### Useful commands

| Command | Why use it? |
|---------|-------------|
| `yarn build` | compile typescript to js |
| `yarn watch` | watch for changes and compile |
| `yarn test` | perform the jest unit tests |
| `cdk deploy` | deploy this stack to your default AWS account/region |
| `cdk diff` | compare deployed stack with current state |
| `cdk synth` | emits the synthesized CloudFormation template |

## Caveats

- This whole setup will produce costs for running it, so think twice before spinning it up.
- - I am not actively working on this anymore. Feel free to fork and enhance the whole setup.
- This was my first time using Python and the AWS CDK, so you will most certainly find super strange things that I've done in this code base. I am sorry to offend you, dear people who do not just hack stuff and kick things until they are working 🙈 If you improve this: Tell me so I can learn from my own mistakes and other people's wisdom!
- I am pretty sure several lambda functions etc could work better if only I had more knowledge about both Python and AWS 🤷🏼‍♂️
- There are some bits of historical analysis lambdas in here. I never made it to completing these. If you do not plan to do any analysis, feel free to remove this part. Also, you could then [set a TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html) for each stock entry in the DynamoDB to have it cleaned up automatically. I had that enabled for a while before I thought I'd do the historical analysis. So I decided to keep the data.
- The timing for sending the email etc. fits to European (german) time, you might want to adjust it to your needs.
- I had a list of beta test subscribers inserted manually in the `dailyEmail` Lambda. You might want to read subscribers from a separate database. Which also would enable features like subscription via some website and unsubscribes etc. Also, deploying the Lambda because you add/remove someone from the subscriber list is really annyoing 😆
- The email itself is raw email HTML (ewwww) since I couldn't get [MJML](http://mjml.io/) working in a Lambda. You can surely find better ways to create HTML emails within Python. Or switch that function to NodeJS or whatever you prefer.
- Remember to fill in a sender and receipients in the email lambda.
