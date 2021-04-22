drop table PROBED_POINTS;
create table PROBED_POINTS (
id integer primary key autoincrement,
measurement_id integer not null ,
x real not null,
y real not null,
z real not null
);