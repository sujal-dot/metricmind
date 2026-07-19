
cube(`DimCustomer`, {
  sql: `SELECT * FROM public.dim_customer`,
  
  joins: {
    
  },

  measures: {
    count: {
      type: `count`,
      drillMembers: [customerId, customerName, segment]
    }
  },

  dimensions: {
    customerKey: {
      sql: `customer_key`,
      type: `number`,
      primaryKey: true
    },
    
    customerId: {
      sql: `customer_id`,
      type: `string`
    },
    
    customerName: {
      sql: `customer_name`,
      type: `string`
    },
    
    segment: {
      sql: `segment`,
      type: `string`
    },
    
    createdAt: {
      sql: `created_at`,
      type: `time`
    }
  },
  
  dataSource: `default`
});
