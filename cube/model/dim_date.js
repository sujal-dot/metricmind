
cube(`DimDate`, {
  sql: `SELECT * FROM public.dim_date`,
  
  joins: {
    
  },

  measures: {
    
  },

  dimensions: {
    dateKey: {
      sql: `date_key`,
      type: `number`,
      primaryKey: true
    },
    
    fullDate: {
      sql: `full_date`,
      type: `time`
    },
    
    dayOfMonth: {
      sql: `day_of_month`,
      type: `number`
    },
    
    month: {
      sql: `month`,
      type: `number`
    },
    
    monthName: {
      sql: `month_name`,
      type: `string`
    },
    
    year: {
      sql: `year`,
      type: `number`
    },
    
    quarter: {
      sql: `quarter`,
      type: `string`
    },
    
    dayOfWeek: {
      sql: `day_of_week`,
      type: `number`
    },
    
    weekNumber: {
      sql: `week_number`,
      type: `number`
    },
    
    isWeekend: {
      sql: `is_weekend`,
      type: `boolean`
    }
  },
  
  dataSource: `default`
});
