# ARRBHack-2018
data hacking for the ARRB Hack - solving transport and infrastructure related problems

## Intro aka TLDR;
This hackathon project was done in about 24 hours for the 'Cycling' and 'Safety' challenges. It tries to solve the problem of cyclist safety via a route planning webapp. If you are not keen on all the technical details, I have made a [presentation about the key things](https://docs.google.com/presentation/d/1qDGI-7CLiB1UBZZBLWGaRyLSzqfIjbi5xozprUsvHWE/view#slide=id.g38fd48d78b_0_199). Also, there's a [prototype running](http://cycling-routes-brisbane.surge.sh) for the Brisbane area - **disclaimer:** safety calculations take about 90-120s, so leave that loading running on the page.  

## Content
* Problem and results
* Tooling and solution process
* Future improvements


### Problem and results
I started to do some research around safety statistics and cyclists a few days before the hackathon. I also got familiar with the [Queensland open data](https://docs.google.com/spreadsheets/d/1nz4M9bRcPgEyS5b_hDjI7RjjAQ7eM9GeUxrU2TLlNdY/edit?usp=sharing) that was available for this topic and identified a problem that was appealing to me.

---
##### More experienced cyclists have a bigger chance to be in right in a fatal or serious incident.
---

From this problem, I identified that commuters who cycle everyday could be in a quite large risk, as both the demographic of this group and the behavior would fit into the problem. I decided to use machine learning to predict the potential risk a cyclist has on a route in a given time based on historical data.

So the question I proposed was: _assuming that every point on the road will have an accident at one point in time, what is the likelihood that the accident is a severe incident and a cyclist is involved?_

Over a few hours, I iterated over 11 ML models that I've built using AWS. These models had different feature sets, and were based on logistic regression to determine whether a portion of a route would have an accident or not. Below are the results that came out of these iterations:

Model | Number of features | Precision | Recall | Accuracy | F1
--- | --- | --- | --- | --- | ---
1 | 14 | 0.4286 | 0.003 | 0.982 | 0.006
2 | 14 | 0.5 | 0.019 | 0.9804 | 0.0038
3 | 14 | 1 | 0 | 0.9804 | 0
4 | 13 | 0.4706 | 0.0074 | 0.9803 | 0.0146
5 | 12 | 0.625 | 0.049 | 0.9813 | 0.0909
6 | 10 | 0.5 | 0.0019 | 0.9811 | 0.0038
7 | 8 | 0.5463 | 0.046 | 0.9535 | 0.0849
8 | 12 | 0.6713 | 0.668 | 0.6773 | 0.6696
*9* | *8* | *0.82* | *0.8169* | *0.7389* | *0.8184*
10 | 10 | 0.6605 | 0.6757 | 0.6754 | 0.668
11 | 10 | 0.6621 | 0.6608 | 0.6634 | 0.6614

### About the process
This repo uses public / open source datasets and [Jupyter notebooks](http://jupyter.org/) to process and visualise them.

If you haven't used Jupyter before, I recommend this easy getting started guide: [Jupyter Notebook Beginner Guide](https://jupyter-notebook-beginner-guide.readthedocs.io/).

I used the prebuilt ML model deployments of AWS as it was a quick and easy way to get started with the process, and produce an endpoint that I can use for the prototype.

After finding a suitable ML model candidate, I exposed its endpoint within the environment set up for the project, and used serverless (framework) to run the data pipeline around it.

There are a few lambdas in the process:

1. _calculate-route_ lambda function takes the parameters from the request that comes from the front end, submits them to the HERE api route planning endpoint, and pushes back the route to the front end. Based on this route that came back from HERE, it also submits a batch request to get address for each geolocation within the route.
2. _here-get-batch_ lambda function gets triggered, when the HERE api sends an email update about the status of the batch process with the link to download the results from. This lambda downloads the contents to an S3 bucket.
3. _prepare-prediction-request_ lambda function does the feature engineering for the model that I have previously chosen, with the data collected from the front end and the batch address requests. It saves all as a .csv file, which then gets fed into the model.
4. _get-final-json_ lambda function wakes up when the ML model has finished the prediction and has an output ready. This lambda then turns the prediction result to a format that the front end can deal with, and saves it as a json to an S3 bucket. While all this was happening, the front end has been polling for this json file the whole time, based on an id that was originally returned by the first lambda.

### Future improvements
- Speed is a major issue, I should really build and deploy my own model so that it's easier to keep track of times. Some things are a little black box-y about AWS ML now, which means that about 70% of the time actually goes for the prediction.
- Improving the model. When I started this project, I didn't know much about other type of solutions, so I think today I would try out SVM instead of a simple logistic regression.
- Better commiting / commenting and generally presenting the process. I found it challenging that data exploration is a chunky process and it's hard to commit often in a meaningful way.
