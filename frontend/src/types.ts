export type User = {
  id: number;
  email: string;
  role: string;
  status: string;
};

export type Equipment = {
  id: number;
  name: string;
  asset_tag: string;
  category_id: number;
  category_name: string;
  status: string;
};
