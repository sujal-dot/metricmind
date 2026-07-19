
const process = require('process');

module.exports = {
  processSqlTemplates: true,
  scheduledRefreshTimer: 60,
  scheduledRefreshTimeZones: ['UTC'],
  scheduledRefreshConcurrency: null,
  dbType: ({ dataSource }) => {
    return process.env.CUBEJS_DB_TYPE || 'postgres';
  },
  schemaVersion: ({ authInfo }) => {
    return '1';
  },
  queryRewrite: (query, { securityContext }) => {
    return query;
  },
  contextToAppId: ({ securityContext }) => {
    return `metricmind_app`;
  },
  preAggregationsSchema: `pre_aggregations`,
  allowDuplicateQueriesFromUserIds: [],
  // You can set up JWT authentication here if needed
  // jwt: {
  //   key: process.env.CUBEJS_API_SECRET,
  //   algorithms: ['HS256'],
  // }
};
