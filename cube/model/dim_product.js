
cube(`DimProduct`, {
  sql: `SELECT * FROM public.dim_product`,
  
  joins: {
    
  },

  measures: {
    count: {
      type: `count`,
      drillMembers: [productId, productName, category]
    }
  },

  dimensions: {
    productKey: {
      sql: `product_key`,
      type: `number`,
      primaryKey: true
    },
    
    productId: {
      sql: `product_id`,
      type: `string`
    },
    
    productName: {
      sql: `product_name`,
      type: `string`
    },
    
    category: {
      sql: `category`,
      type: `string`
    },
    
    subCategory: {
      sql: `sub_category`,
      type: `string`
    },
    
    createdAt: {
      sql: `created_at`,
      type: `time`
    }
  },
  
  dataSource: `default`
});
