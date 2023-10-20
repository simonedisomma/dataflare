# Load YAML datacards (in a real scenario, you might load this from a file)
datacard1_yaml = '''
title: "COVID-19 Trends in New York State"
datasource:
  type: "API"
  endpoint: "https://covid-api.example.com/new-york"
query:
  fields: 
    - "date"
    - "confirmed_cases"
    - "deaths"
  filters:
    - "date >= '2022-01-01'"
visualization:
  type: "chart"
  x_axis: "date"
  y_axis: 
    - "confirmed_cases"
    - "deaths"
  chart_type: "line"
'''

datacard1 = yaml.safe_load(datacard1_yaml)
render_chart_from_datacard(datacard1, "div1")
