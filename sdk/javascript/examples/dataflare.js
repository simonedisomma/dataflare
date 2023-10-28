async function renderDataCard(targetDivId = 'datacard') {
    const yamlText = `dataCard1:
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
        chart_type: "line"`;
  
    const dataCard = jsyaml.load(yamlText);
    const endpoint = dataCard.datasource.endpoint;
    const fields = dataCard.query.fields.join(',');
    const filters = encodeURIComponent(dataCard.query.filters.join(' AND '));
  
    const response = await fetch(`${endpoint}?fields=${fields}&filters=${filters}`);
    const data = await response.json();
  
    const labels = data.map(item => item.date);
    const confirmedCasesData = data.map(item => item.confirmed_cases);
    const deathsData = data.map(item => item.deaths);
  
    const chart = echarts.init(document.getElementById(targetDivId));
  
    const option = {
      title: {
        text: dataCard.title
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: labels
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: 'Confirmed Cases',
          type: dataCard.visualization.chart_type,
          data: confirmedCasesData
        },
        {
          name: 'Deaths',
          type: dataCard.visualization.chart_type,
          data: deathsData
        }
      ]
    };
  
    chart.setOption(option);
  }
  
  renderDataCard();
  