-- read table
local data = io.open("results.csv", "r")

local df_damping = {}
local df_tolerance = {}
local df_iterations = {}
local df_time = {}
local df_p_min = {}
local df_p_25 = {}
local df_p_50 = {}
local df_p_75 = {}
local df_p_max = {}
local i = 0
for line in data:lines() do
-- damping,tolerance,iterations,time,p_min,p_25,p_50,p_75,p_max
    local damping, tolerance, iterations, time, p_min, p_25, p_50, p_75, p_max = line:match("([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+)")
    print(tolerance)
    if tolerance == Tolerance then
         table.insert(df_damping, damping)
         table.insert(df_tolerance, tolerance)
         table.insert(df_iterations, iterations)
         table.insert(df_time, time)
         table.insert(df_p_min, p_min)
         table.insert(df_p_25, p_25)
         table.insert(df_p_50, p_50)
         table.insert(df_p_75, p_75)
         table.insert(df_p_max, p_max)
    end
    i = i + 1
end
data:close()

print("damping: " .. #df_damping)

for i = 1, #df_damping do
    tex.print("\\addplot+[boxplot prepared={")
    tex.print("lower whisker=" .. df_p_min[i] .. ",")
    tex.print("lower quartile=" .. df_p_25[i] .. ",")
    tex.print("median=" .. df_p_50[i] .. ",")
    tex.print("upper quartile=" .. df_p_75[i] .. ",")
    tex.print("upper whisker=" .. df_p_max[i] .. "}")
    tex.print("] coordinates {};")
end
