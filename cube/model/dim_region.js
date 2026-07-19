
cube(`DimRegion`, {
  sql: `SELECT * FROM public.dim_region`,
  
  joins: {
    
  },

  measures: {
    count: {
      type: `count`,
      drillMembers: [region, state, city]
    }
  },

  dimensions: {
    regionKey: {
      sql: `region_key`,
      type: `number`,
      primaryKey: true
    },
    
    country: {
      sql: `country`,
      type: `string`
    },
    
    state: {
      sql: `state`,
      type: `string`
    },
    
    city: {
      sql: `city`,
      type: `string`
    },
    
    region: {
      sql: `region`,
      type: `string`
    },
    
    createdAt: {
      sql: `created_at`,
      type: `time`
    }
  },
  
  dataSource: `default`
});
