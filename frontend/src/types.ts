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

export type Reservation = {
  id: number;
  user_id: number;
  equipment_id: number;
  equipment_name: string;
  start_date: string;
  end_date: string;
  status: string;
};

export type Category = {
  id: number;
  name: string;
};

export type AdminReservation = {
  id: number;
  user_id: number;
  user_email: string;
  equipment_id: number;
  equipment_name: string;
  start_date: string;
  end_date: string;
  status: string;
};
