# Datasets Documentation

## Introduction

Datasets in this project are data files that can be used as local sources for Data Cards. The primary supported formats are CSV and JSON.

## Structure

### CSV Datasets

- **File Extension**: `.csv`
- **Description**: Comma-separated values file that can be read into a Pandas DataFrame.

#### Fields

- Column names should match those expected by Data Cards that use them.
  
#### Example

```csv
date,confirmed_cases,deaths
2022-01-01,100,2
2022-01-02,150,4
...
```

#### JSON Datasets
File Extension: .json
Description: JSON file that can be read into a Pandas DataFrame.
Fields
JSON keys should match those expected by Data Cards that use them.
Example

```javascript
[
  {
    "date": "2022-01-01",
    "confirmed_cases": 100,
    "deaths": 2
  },
  {
    "date": "2022-01-02",
    "confirmed_cases": 150,
    "deaths": 4
  }
]
```

#### Directory
Place the datasets in the datasets/ directory in the root of the project.

#### Usage
In the Data Card, specify the local dataset by using the relative filepath as the endpoint in the datasource section.

#### Naming Convention
Use underscore _ to separate words in dataset filenames.

#### Important Notes
Ensure that the data types and formats in the datasets align with those expected by the Data Cards that will use them.