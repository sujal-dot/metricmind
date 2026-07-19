
cube(`DimEmployee`, {
  sql: `SELECT * FROM public.dim_employee`,
  
  joins: {
    
  },

  measures: {
    count: {
      type: `count`,
      drillMembers: [employeeId, employeeName]
    }
  },

  dimensions: {
    employeeKey: {
      sql: `employee_key`,
      type: `number`,
      primaryKey: true
    },
    
    employeeId: {
      sql: `employee_id`,
      type: `string`
    },
    
    employeeName: {
      sql: `employee_name`,
      type: `string`
    },
    
    department: {
      sql: `department`,
      type: `string`
    },
    
    createdAt: {
      sql: `created_at`,
      type: `time`
    }
  },
  
  dataSource: `default`
});
