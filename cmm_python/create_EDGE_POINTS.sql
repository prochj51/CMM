drop table EDGE_POINTS;
create table EDGE_POINTS (
id integer primary key autoincrement,
measurement_id integer not null ,
x0 real not null,
y0 real not null,
x1 real,
y1 real,
r real
);