# Data Card Documentation

## Introduction

A Data Card is a YAML file that provides a concise and human-readable description of how data should be queried and visualized. The primary components include the title, data source, query, and visualization settings.

## Structure

### `title`

- **Type**: String
- **Description**: The title of the data card.

### `datasource`

- **Type**: Object
- **Description**: Describes the data source from which to pull data.

  - `type`: The type of data source, such as `"API"` or `"CSV"`.
  - `endpoint`: The URL or filepath of the data source.

### `query`

- **Type**: Object
- **Description**: Defines the query parameters to fetch the right set of data.

  - `fields`: Array of fields to select.
  - `filters`: Array of conditions to apply.

### `visualization`

- **Type**: Object
- **Description**: Specifies how the data should be visualized.

  - `type`: Type of visualization, e.g., `"chart"`.
  - `x_axis`: The field to be plotted on the x-axis.
  - `y_axis`: Array of fields to be plotted on the y-axis.
  - `chart_type`: Specific chart type like `"line"` or `"bar"`.

## Example

Here's a sample data card for visualizing COVID-19 trends in New York:

```yaml
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
```

