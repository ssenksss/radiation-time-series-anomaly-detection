export const dashboardData = {
  header: {
    title: 'Anomaly Detection System',
    subtitle:
        'Early warning simulation for radiation monitoring using machine learning.',
  },

  current: {
    label: 'Current Level',
    value: '0.75',
    unit: 'µSv/h',
    change: '+0.06 over the last 24h',
    source: 'Source: radiation_data.csv',
    datasetLabel: 'View Dataset',
  },

  chart: {
    title: 'Radiation Levels Over Time',
    legend: {
      radiation: 'Radiation Levels',
      anomalies: 'Detected Anomalies',
      threshold: 'Anomaly Threshold',
    },
    yAxis: ['0.8', '0.6', '0.4', '0.3', '0.1'],
    xAxis: ['Apr 16', 'Apr 17', 'Apr 18', 'Apr 20', 'Apr 21', 'Apr 22', 'Apr 23'],
  },

  alert: {
    title: 'ANOMALY DETECTED',
    description: 'Elevated radiation level detected. Threshold exceeded.',
    buttonLabel: 'ACKNOWLEDGE',
  },

  stats: [
    {
      title: 'Total Anomalies',
      value: '6',
      meta: '+2 today',
      icon: '⚠',
      danger: true,
      hasButton: false,
      buttonLabel: '',
    },
    {
      title: 'Current Level',
      value: '0.75 µSv/h',
      meta: '+0.06 over the last 24h',
      icon: '◉',
      danger: false,
      hasButton: false,
      buttonLabel: '',
    },
    {
      title: 'Testing Accuracy',
      value: '93.5%',
      meta: 'Isolation Forest',
      icon: '⌁',
      danger: false,
      hasButton: true,
      buttonLabel: 'Test Models',
    },
  ],

  anomalyDetails: {
    title: 'Anomaly Details',
    columns: ['Timestamp', 'Radiation Level', 'Flag', 'Status'],
    rows: [
      {
        timestamp: 'Apr 23, 2024, 16:30',
        level: '0.75 µSv/h',
        tag: 'NEW',
        status: 'Anomaly',
      },
      {
        timestamp: 'Apr 22, 2024, 11:45',
        level: '0.80 µSv/h',
        tag: 'NEW',
        status: 'Anomaly',
      },
    ],
  },

  anomaliesLog: {
    title: 'Anomalies Log',
    items: [
      {
        timestamp: 'Apr 23, 2024, 11:45',
        value: '0.76 µSv/h',
        isNew: true,
      },
      {
        timestamp: 'Apr 22, 2024, 16:30',
        value: '0.80 µSv/h',
        isNew: true,
      },
      {
        timestamp: 'Apr 22, 2024, 11:45',
        value: '0.75 µSv/h',
        isNew: false,
      },
    ],
  },

  modelTesting: {
    title: 'Model Testing',
    accuracyLabel: 'Recent Accuracy:',
    accuracyValue: '93.4%',
    source: 'Source: isolation_forest_results.json',
    action: 'Latest evaluation',
    bars: [
      { percent: '93.4%', className: 'large' },
      { percent: '87.9%', className: 'medium' },
      { percent: '81.2%', className: 'small' },
    ],
    labels: ['Isolation Forest', 'LOF'],
  },

  common: {
    viewAll: 'View All',
  },
}
