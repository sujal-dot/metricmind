
cube(`FactSales`, {
  sql: `SELECT * FROM public.fact_sales`,
  
  joins: {
    DimCustomer: {
      sql: `${CUBE}.customer_key = ${DimCustomer.customerKey}`,
      relationship: `belongsTo`
    },
    DimProduct: {
      sql: `${CUBE}.product_key = ${DimProduct.productKey}`,
      relationship: `belongsTo`
    },
    DimDate: {
      sql: `${CUBE}.date_key = ${DimDate.dateKey}`,
      relationship: `belongsTo`
    },
    DimRegion: {
      sql: `${CUBE}.region_key = ${DimRegion.regionKey}`,
      relationship: `belongsTo`
    },
    DimEmployee: {
      sql: `${CUBE}.employee_key = ${DimEmployee.employeeKey}`,
      relationship: `belongsTo`
    }
  },

  measures: {
    count: {
      type: `count`,
      drillMembers: [orderId, salesAmount, quantity]
    },
    
    revenue: {
      sql: `sales_amount`,
      type: `sum`,
      title: `Revenue`
    },
    
    profit: {
      sql: `profit_amount`,
      type: `sum`,
      title: `Profit`
    },
    
    totalOrders: {
      sql: `order_id`,
      type: `countDistinct`,
      title: `Total Orders`
    },
    
    totalQuantity: {
      sql: `quantity`,
      type: `sum`,
      title: `Total Quantity Sold`
    },
    
    discountAmount: {
      sql: `sales_amount * discount`,
      type: `sum`,
      title: `Total Discount Amount`
    },
    
    averageOrderValue: {
      sql: `${revenue} / NULLIF(${totalOrders}, 0)`,
      type: `number`,
      title: `Average Order Value`
    },
    
    averageProfit: {
      sql: `${profit} / NULLIF(${totalOrders}, 0)`,
      type: `number`,
      title: `Average Profit per Order`
    },
    
    margin: {
      sql: `NULLIF(${profit}, 0) / NULLIF(${revenue}, 0)`,
      type: `number`,
      title: `Profit Margin (%)`,
      format: `percent`
    },
    
    totalCustomers: {
      sql: `customer_key`,
      type: `countDistinct`,
      title: `Total Customers`
    }
  },

  dimensions: {
    salesKey: {
      sql: `sales_key`,
      type: `number`,
      primaryKey: true
    },
    
    orderId: {
      sql: `order_id`,
      type: `string`
    },

    salesAmount: {
      sql: `sales_amount`,
      type: `number`,
      shown: false
    },

    quantity: {
      sql: `quantity`,
      type: `number`,
      shown: false
    },
    
    createdAt: {
      sql: `created_at`,
      type: `time`
    },

    shipMode: {
      sql: `ship_mode`,
      type: `string`
    }
  },
  
  dataSource: `default`
});
