# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite")
Base=automap_base()

# reflect an existing database into a new model
Base.prepare(autoload_with=engine)


# reflect the tables
Station=Base.classes.station

# Save references to each table
Measurement=Base.classes.measurement

# Create our session (link) from Python to the DB
session=Session(engine)

#################################################
# Flask Setup
#################################################

app=Flask(__name__)
@app.route("/")
def welcome():
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"---------------------------------------------<br/>"
        f"Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.Return the JSON representation of your dictionary.<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"---------------------------------------------<br/>"
        f"Return a JSON list of stations from the dataset.<br/>"
        f"//api/v1.0/stations<br/>"
        f"---------------------------------------------<br/>"
        f"Query the dates and temperature observations of the most-active station for the previous year of data.Return a JSON list of temperature observations for the previous year<br/>"
        f"/api/v1.0/tobs<br/>"
        f"---------------------------------------------<br/>"
        f"Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.<br/>"
        f"For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.<br/>"
        f"For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )


#Precipiattion analysis for last 12 months data
@app.route("/api/v1.0/precipitation")
def precipitation():
    #calculating the end date for measurement,and converting this into date time object for futhur caculation
    end_date_string=session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    end_date=end_date_string[0]
    end_date_object=dt.datetime.strptime(end_date, "%Y-%m-%d")
    year = int(end_date_object.strftime('%Y'))
    month = int(end_date_object.strftime('%m'))
    #Checking if year is leap, then 366 days ahead, if not then 365 days ahead, calculting satrt_date based on this
    if(year%4==0):
        start_date_object=end_date_object-dt.timedelta(days=366)

    else:
        start_date_object=end_date_object-dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    data=session.query(Measurement.date,Measurement.prcp).filter(Measurement.date>start_date_object,Measurement.prcp != None).order_by(Measurement.date).all()
    # Convert the result to a dictionary with lists of precipitation values
    result_dict = {}

    for date, prcp in data:
        result_dict.setdefault(date, []).append(prcp)

    return jsonify(result_dict)

#Returning a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def station_list():
    st_list = [s.station for s in session.query(Station.station).distinct()]
    return jsonify(st_list)
    

#Calculating Most active station details
@app.route("/api/v1.0/tobs")
def active_station():
    active_station=session.query(Measurement.station,func.count(Measurement.date)).group_by(Measurement.station).order_by(func.count(Measurement.date).desc()).first()
    # Extract the station code of the most active station
    station_code = active_station[0]
    #Calculating the end date in relevant to most active station and converting to date time object
    end_date_string=session.query(Measurement.date).filter(Measurement.station == station_code).order_by(Measurement.date.desc()).first()
    end_date=end_date_string[0]
    #end_date_string = session.query(func.max(Measurement.date)).filter(Measurement.station == station_code).first()
    end_date_object = dt.datetime.strptime(end_date, "%Y-%m-%d")
    start_date_object = end_date_object - dt.timedelta(days=365)

    #Quering the data and putting it in dictionary
    data = (
            session.query(Measurement.date, Measurement.tobs)
            .filter(Measurement.station == station_code, Measurement.date > start_date_object, Measurement.tobs != None)
            .order_by(Measurement.date)
            .all()
        )

    #
    result_dict = {
    "station": station_code,
    "temperature_observations": [(date, tobs) for date, tobs in data]
}
    return(result_dict)
    
#Returning a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range
@app.route("/api/v1.0/<start>")
def trip1(start):
    #Calculating start date and end date
    start_date= dt.datetime.strptime(start, '%Y-%m-%d')
    end =  session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    end_date=dt.datetime.strptime(end[0], '%Y-%m-%d')
    trip_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    # Flattening the result using np.ravel and converting it to a list
    trip = list(np.ravel(trip_data))
    # Returning the result as JSON
    return jsonify(trip)

#########################################################################################
@app.route("/api/v1.0/<start>/<end>")
def trip2(start,end):

  # #Calculating start date and end date in the form of date time object     
    start_date= dt.datetime.strptime(start, '%Y-%m-%d')
    end_date= dt.datetime.strptime(end, '%Y-%m-%d')
    trip_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    # Flattening the result using np.ravel and converting it to a list
    trip = list(np.ravel(trip_data))
    # Returning the result as JSON
    return jsonify(trip)

#################################################
# Flask Routes
#################################################
if __name__ == "__main__":
    app.run(debug=True)