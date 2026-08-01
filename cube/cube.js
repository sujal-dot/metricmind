
const process = require('process');

module.exports = {

  // MetricMind keeps Cube model files in cube/model instead of Cube's
  // default cube/schema directory.
  schemaPath: 'model',
  // Local dev does not need background refresh jobs, and disabling them avoids
  // Cube Store startup noise while the API and Playground remain fully usable.
  scheduledRefreshTimer: false,
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
  // You can set up JWT authentication here if needed
  // jwt: {
  //   key: process.env.CUBEJS_API_SECRET,
  //   algorithms: ['HS256'],
  // }
};
