"""
This example implements the LTL Pooling model discussed in Zone Skipping, LTL Pooling & Challenge 9 using Python, PulP and pyodbc. 
Python is the coding language
PuLP is the modeling language and
pyodbc provides the database connectivity to extract the data from Access 

What you need:
Python (I'm using 32bit Python 2.7), 
PuLP and 
pyodbc (I used pyodbc 3.0.7 for 32bit Windows and Python 2.7)

I'm putting the data in an Access 2010 database called Retailer2017.accdb with path c:\Data\
You can download Retailer2017.accdb from The class T-Square site under /Resources/CH8-LinearModels. 
"""

""" 
First we need to identify how to find the database. That can be done in a number of ways. The easiest, in my opinion, 
is to use a DSN or Data Source Name. Here are instructions for creating a DSN called Retailer2017. To do that, 
1. Open the Control Panel (I assume you are using Windows)
2. Select Administrative Tools
3. Select (32 bit) Data Sources (ODBC) - unless you've installed 64 bit Access, etc. 
4. On the ODBC Data Source Administrator, select the User DSN tab
5. Click the Add button
6. On the Create New Data Source dialog, select "Microsoft Access Driver (*.mdb, *.accdb)"
7. Click the Finish button
8. In the ODBC Microsoft Access Setup dialog enter Retailer2017 in the Data Source Name field  
9. You may optionally enter a description in the Description field
10. Click the Select... button
11. In the Select Database dialog, navigate to c:\Data\ and select Retailer2017.accdb and click the OK button
12. In the ODBC Microsoft Access Setup dialog click the OK button
13. In the ODBC Data Source Administrator dialog click the OK button

You have successfully created a DSN for the Retailer2017.accdb database

The tools for reading data from and writing answers to the database are in pyodbcconnect.py
PuLP is the Python LP modeling language
"""
import sqlite3
from sqlite3 import Error
from pulp import *


# name of database
database = 'Challenge8.db'


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """


    return None


def get_data_for_table(tablename):
    # create a database connection
    conn = create_connection(database)

    cur = conn.cursor()
    cur.execute("SELECT * FROM " + tablename)

    rows = cur.fetchall()
    # returns a list of lists that contains the rows for each tables
    for row in rows:
        print(row)
    return rows



"""
First, we have Store data. 

We construct a query in Retailer2017.accdb that filters the stores and has the fields
Field         Type          Description
StoreID       Long Integer  Unique identifier for the Store
Size          Double        Size of the store
LTLDirectRate Double        Undiscounted cost per direct LTL shipment from the XDock

"""

# The name of the Query in Retailer2017 that selects the stores
store_tab = 'SelectStores'

print "Reading Store data"
# Get the store data 
store_data = get_data_for_table(store_tab)

""" 
Some Notes: 
I've separated the LTLDirectRate data from the Store Data to allow "future enhancements" that
allow us to have more than one cross dock and so may decide which cross dock 
will serve the store when it is served 'Direct'. This implementation assumes 
the 1st cross dock (with XDockID = 1) is the only cross dock and SelectStores must include 
this data

Note too that this implementation simplifies the "frequency" issue. 
We assume here that all stores are served with the same frequency 
and that frequency is reflected in the LTL Rates (we rated shipments 
of a size determined by the common frequency). 

If we segment the stores by the frequency of shipments, the easiest and 
probably most practical thing to do is handle each segment separately. That works
if our segmentation focuses more on geography than on size. Right! Stores close 
together are candidates to be served out of the same terminal and so to ride on
the same truck out to that terminal and so they'll be served with the same frequency.
 
"""
 

"""
Now let's read the Terminal data. I created this from a list of 
XPO LTL Terminals in the US. 

Notes: 
1. That's a bit odd and probably biases against LTL consolidation 
   in that we're using UPS rates and XPO terminals. XPO would likely 
   give better rates directly from their terminals. UPS rates would 
   include some consideration for picking up the freight and hauling 
   it to one of their terminals. 
2. UPS doesn't provide rates from every ZIP Code where XPO has a 
   terminal -- the two carriers have different geographic focus.
   So I came back and trimmed the list of Terminals to those in ZIP 
   codes UPS serves. 


We construct a query in Retailer2017.accdb that has the fields
Field        Type          Description
TerminalID   Long Integer  Unique identifier for the Terminal
CrowFlies    Double        Distance from the XDock to the Terminal

"""
# The name of the table holding the terminal data
terminal_tab = 'SelectTerminals'

print "Reading Terminal data"
# Get the terminal data 
terminal_data = get_data_for_table(terminal_tab)


#==========================================================================================
"""
Next, let's read in the Lane data. 

We construct a query in Retailer2017.accdb that has the fields
Field        Type          Description
LaneID       Long Integer  Unique identifier for the lane
TerminalID   Long Integer  Unique identifier for the terminal
StoreID      Long Integer  Unique identifier for the store
LTLRate      Double        Undiscounted cost for a single LTL shipment from the terminal to the store


I created this through a series of steps that you can (at least in part) follow in the Database
1. Create_All_Terminal_Store_Lanes creates a table with all the Terminal-Store pairs and the "crow flies" distance between them. 
   I built the Distance function into Access via a Module. This does not include the LTL Rates, obviously.
2. Trim_Terminal_To_Store_Lanes_by_Max_Distance deletes all lanes where the store is more than "Max_Terminal_miles" (a parameter in the Parameters Table) away
   from the terminal. 
3. I used UPSLTLRate to get LTL rates for weekly shipments on those lanes. I did that in Excel -- it's slow and then imported the results back into Lanes
Note: Turns out UPS doesn't serve all these ZIPs so I filtered the terminals to the ones UPS serves

"""
# The name of the table holding the lane data
lane_tab = 'SelectLanes'

print "Reading Lane data"
lane_data = get_data_for_table(lane_tab)


'''
We can  use the where_clause to get various slices of the lane data and so organize 
by terminal. This constructs a "slice" of the lanes from each terminal. And then constructs
a "slice" of the lanes to each store.

Pretty cool that we can apply a WHERE clause to an existing Query
'''
print "Constructing terminal oriented version"
terminallanes = dict()
for termid in terminal_data:
    where_string = 'TerminalID = %s' \
            % (str(termid))
    terminallanes[termid]=database.get_table(lane_tab, where_string)

    
print "Constructing store oriented version"
# and we can organize by store
storelanes = dict()
for storeid in store_data:
    where_string = 'StoreID = %s' \
            % (str(storeid))
    storelanes[storeid]=database.get_table(lane_tab, where_string)

#==========================================================================================
"""
Finally, let's read in the Parameters. These are in the Params Table 

The Parameters table in Retailer2017.accdb has the fields
Field            Type          Description
ParameterName    Text          Unique name for the parameter
ParameterValue   Double        Value of the parameter

The parameters of interest are:
Average_Weight: The weight in pounds of a shipment to a store of size 1
Average_Cube: The cubic feet of a shipment to a store of size 1
Truck_Load_capacity_lbs: The capacity of a truck in pounds
Truck_Load_capacity_cubic_ft: The capacity of a truck in cubic feet.
Truck_Load_cost_per_mile: The cost per mile with out Truck load carrier
Fuel_Surcharge: The fuel surcharge %
BinaryAssignments: Whether we want to serve each store in exactly one way or not.
"""
# The name of the table holding the parameters 
param_tab = 'Params'

print "Reading problem parameters"
# Get the lane data 
param_data = database.get_table(param_tab)

# Here's easy access to some key parameters
# The weight we ship each week to a store of size 1
AvgWeight = param_data['Average_Weight']['ParamValue']
# The weight a truck can hold
TLMaxWeight = param_data['Truck_Load_capacity_lbs']['ParamValue']
# The Cupe we ship each week to a store of size 1
AvgCube= param_data['Average_Cube']['ParamValue']
# The cubic capacity of a truck
TLMaxCube = param_data['Truck_Load_capacity_cubic_ft']['ParamValue']
# The cost per mile
TLCostPerMile = param_data['Truck_Load_cost_per_mile']['ParamValue']
# The Fuel Surcharge
FuelSurcharge = param_data['Fuel_Surcharge']['ParamValue']
# The LTL Discount %
LTLDiscount = param_data['LTL_Discount']['ParamValue']
# The BinaryAssignments indication
BinaryAssignments = param_data['BinaryAssignments']['ParamValue']

#====================================================================================================
#====================================================================================================
#====================================================================================================  
""" 
Now let's build the model - 
"""

# The Trucks Variables, one for each terminal, telling us how many trucks to run from the DC to that terminal
print "Building the model"
Truck_vars = pulp.LpVariable.dicts("Trucks", terminal_data, 0, None, LpInteger)

# The Assign Variables, one for each lane 
# These tell us which stores are served by which terminals
if BinaryAssignments == 1.0:
    Assign_vars = pulp.LpVariable.dicts("Assign", lane_data, 0, 1, LpInteger) 
else: 
    Assign_vars = pulp.LpVariable.dicts("Assign", lane_data, 0, None, LpContinuous) 

# Do we need other variables? Which ones? 
    
# Create the problem to minimize
prob = pulp.LpProblem("LTLPooling", LpMinimize) 

# Create the objective as the sum of the LTL rates from the terminals to the stores + 
#            the TL rates we pay to the terminals
# Is that all the costs we need to worry about? 
total_cost = pulp.lpSum(Assign_vars[laneid]*lane_data[laneid]['LTLRate']*(1.0-LTLDiscount) for laneid in lane_data) + \
             pulp.lpSum(Truck_vars[termid]*terminal_data[termid]['CrowFlies']*TLCostPerMile*(1.0+FuelSurcharge) for termid in terminal_data)
                         
prob+=total_cost, "Minimize Total Transportation Cost"  

# The constraints


# The number of trucks required to carry the weight to each terminal
# below we get the store id from the lane and use that to look up the store size
for termid in terminal_data:
    constraint = (pulp.lpSum([Assign_vars[laneid]*store_data[lane_data[laneid]['StoreID']]['Size'] for laneid in terminallanes[termid]]) - Truck_vars[termid]*TLMaxWeight/AvgWeight) <= 0
    prob+= constraint, "Trucks by Weight Constraint:%s" % str(termid)

# The number of trucks required to carry the cube to each terminal


# Let's add constraints that sharpen the relationship between Assignments and Trucks
    
    # Let's finish up
    # The problem data is written to an .lp file

prob.writeLP("LTLConsolidation.lp")

# ============================================================================================================
print "Solving the problem"
# The problem is solved using PuLP's choice of Solver
prob.solve()
# The status of the solution is printed to the screen, i.e., optimal, infeasible, unbounded,
print "Status:", pulp.LpStatus[prob.status]
print "Writing the solution to the database"
# 
# ============================================================================================================
# Let's empty out any previous solutions to avoid possible confusion. 


"""
This clears out all previous solutions, so beware! You'll lose all previous solution data.
"""
# This sets 'Assigned' to 0 in every row of lane_tab
database.update_table('Lanes', 'Assigned', 0)

# This sets 'LTLDirect' to 0 in every row of store_tab
database.update_table('Stores', 'LTLDirect', 0)

# This sets 'Trucks' to 0 in every row of terminal_tab
database.update_table('Terminals', 'Trucks', 0)

# run through the Assign variable and map them back to the lanes and update the database
# The Truck_vars
for termid in terminal_data:
    termval = Truck_vars[termid].varValue
    if termval > 0:
        where_string = 'TerminalID = %s' % termid
        database.update_table('Terminals', 'Trucks', termval, where_string)

# The Assign_vars
for laneid in lane_data:
    laneval = Assign_vars[laneid].varValue
    if laneval > 0:
        where_string = 'LaneID =%s' % str(laneid)
        # update_table updates the field 'Assigned' of the table lane_table with value of the variable in the row corresponding to laneid
        database.update_table('Lanes','Assigned', laneval, where_string)
        
# We may need to write out solutions for any other variables we added
        
# The optimised objective function value is printed to the screen - we might want to put it in the database somewhere too
print "Total Cost = ", pulp.value(prob.objective)  