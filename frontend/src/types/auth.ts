export type User = {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
};
