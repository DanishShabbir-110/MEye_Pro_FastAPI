create Database [M-EYE Pro]

create table [User]
(
UID varchar(150) constraint pk_user primary key,
[Full Name] varchar(250),
Password varchar(250),
Role varchar(250),
[Profile Image Url] varchar(250),
Profile_Created_Time time,
Profile_Created_Date date

)
create table Student
(
Regno varchar (150) constraint pk_stud primary key ,
Constraint fk_std foreign key(Regno) references [User](UID) ,
Semester int,
Discipline varchar(10),
Section varchar (1)
)
create table [Student Pic]
(
[Pic id] varchar(100) constraint stdpic Primary key ,
[Pic Url] varchar(250),
[regno] varchar(150)  foreign key references Student (Regno)
)

create table Teacher
(
TID varchar (150) constraint pk_teacher primary key,
constraint fk_th foreign key (TID) references [User](UID)
)
create table [Teacher Pic]
(
[Pic id] varchar(100)  Primary key ,
[Pic Url] varchar(250),
[Teacher id]varchar(150) foreign key references Teacher (TID)
)

create table Admin
(
AID varchar (150) constraint pk_admin primary key,
constraint fk_admin foreign key (AID) references [User](UID)
)

create table DataCell
(
[DC ID] varchar (150) constraint pk_dc primary key,
constraint fk_dc foreign key ([DC ID]) references [User](UID),
)

create table Director
(
[Dir ID] varchar (150) constraint pk_dirc primary key,
constraint fk_dirc foreign key ([Dir ID]) references [User](UID),
)

create table Course 
(
CId varchar (150) constraint pk_crs primary key,
[Course Name] varchar (150),
[Credit Hours] varchar (50)
)

create table Allocation
(
Aid int primary key identity(1,1),
Cid varchar (150),
Tid varchar (150),
Discipline varchar (50),
[Session] varchar (50),
Section varchar (5),
Semester int,
[Year] int,
constraint fk_Teacher foreign key (Tid) references Teacher (TID),
constraint fk_Course foreign key (Cid) references Course (CId),
)
create table Enrollment
(
[Enrollment Id] int primary key identity(1,1),
[Student Id] varchar (150),
[Course Id] varchar(150),
section varchar(1),
Semester int,
Session Varchar(100),
constraint fk_stid foreign key ([Student Id]) references Student (Regno),
constraint fk_cid foreign key ([Course Id]) references Course (CId)
)
create table DVR
(

MAC varchar(150) constraint pk_mac primary key ,
[IP] varchar (150),
Name varchar (100),
channel int,
Password varchar(150)
)
create table [DVR Management]
(
[Admin Id] varchar (150) constraint fk_AdminID foreign key ([Admin Id]) references Admin(AID),
[DVR Id] varchar (150) constraint fk_DVRID foreign key ([DVR Id]) references DVR(MAC),
[Date] date,
[Time] time,
constraint pk_NVRManagement primary key ([Admin Id],[DVR Id])
)

create table Venue 
(
[Venue Id] varchar(10) constraint fk_venue primary key ,
[Venue Type] varchar (50),
)

create table Camera 
(
MAC varchar(150) constraint pk_camMac primary key ,
[Camera Type] varchar(100),
[Channel No] int,
Resolution varchar(50),
Status varchar (20),
[IP] varchar (50),
[DVR Id] varchar(150) constraint fk_DVRS foreign key ([DVR Id]) references DVR([MAC]),
[Venue Id] varchar(10) constraint fk_venueid foreign key ([Venue Id]) references Venue([Venue Id])
)
create table TimeTable 
(
[Schedule Id] int identity (1,1) constraint pk_timetable primary key , 
Session varchar(50),
[Year] int ,
Discipline varchar (50),
Section varchar (3),
Semester int,
[Day] varchar(10),
[Class Start Time] varchar (20),
[Class End Time] varchar (20),


[Course Id] varchar (150) constraint fk_crsidtt foreign key ([Course Id]) references Course (CId),
[Teacher Id] varchar (150) constraint fk_tntt foreign key ([Teacher Id]) references Teacher (TID),
[Venue Id] varchar(10) constraint fkvnidtt foreign key ([Venue Id]) references Venue([Venue Id]),
[Version] int
)
create Table [Teacher CHR]
(
[CHR Id] int Identity(1,1) primary key,
[Schedule Id] int foreign key references TimeTable([Schedule Id]),
[Date] Date,
[Time In] time,
[Time Out] time,
[Stand Time] time,
[Sit Time] time,
status varchar(30),
claim bit not null default 0,

)
select * from DVR
create table [Teacher Recording]
(
[Record Id] varchar (100) primary key,
[Media Path] Varchar(250),
[Date] Date,
[CHR] int foreign key references [Teacher CHR]([CHR Id])
)
Create table [Student Attendance]
(
[AttendanceId] int identity (1,1) primary key ,
[Reg No] varchar(150) foreign key references Student(Regno),
[Schedule Id] int foreign key references TimeTable([Schedule Id]),
[Date] date ,
claim bit  not null default 0
)
create Table [Schedule Media]
(
[Schedule Media Id] int identity (1,1) primary key,
[Schedule Id] int foreign key references TimeTable([Schedule Id]),
[Media Taken At] time ,
[Media Path] varchar(100)
)
drop table [Schedule Media]
create table [Student Recording]
(
[Record Id] varchar(100) primary key ,
Regno varchar (150) foreign key references Student(Regno),
[Schedule Media Id] int foreign key references [Schedule Media]([Schedule Media Id])


)
create Table [Schedule Changes]
 (
[Old Schedule Id] int constraint fk_schdlidC foreign key ([Old Schedule Id]) references TimeTable ([Schedule Id]),
[ChangeSchedule Id] int constraint pk_RidC Primary key identity(1,1),
[New Venue Id] varchar(10),
[Start Time] time,
[End Time] time,
[Reschedule] bit not null default 0,
[Preschedule] bit not null default 0,
[Swap] bit not null default 0,
[Day]varchar(50)
 )
 