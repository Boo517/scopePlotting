% HOW TO USE THIS SCRIPT
% 1) make sure the experimental values section below has the correct info
% 2) in the post processing settings section, make appropiate changes
    % changes to this section are only needed if data is very noisy
    % can run first section of script to plot raw waveforms to find t1 and
    % t2, but they are only used if removeNoise is true
% 3) run the script and select the listing .txt file from the dialog box
    % text file columns: Sample #, DSO1/2 channels, time
    % when exporting .txt from TLA, uncheck unit characters (under Options)
    % to make sure you get absolute time, double click timestamp on listing
    % and a menu will pop up where you can select it (under Column)

% EXPERIMENTAL VALUES
dB1 = 19.82; % attenuation in decibels for BRog1
dB2 = 19.49; % attenuation in decibels for BRog2
R1 = 765500000; % Rogowski coil coefficient for BRog1
R2 = 820000000; % Rogowski coil coefficient for BRog2
% multiplication factors so that trigger and diode are visible (timing)
trigCurrentFactor = 10^4; % trigger on current plot
diodeCurrentFactor = 10^5; % diode on current plot
diodeRawFactor = 10^5; % diode on scope plot

% POST PROCESSING SETTINGS
t1 = -7.188; % time in us where the actual signal starts for BRog1
t2 = -7.188; % time in us where the actual signal starts for BRog2
window = 1; % length of window for loess smoothing (if 1, no smoothing)
removeNoise = false; % baseline noise removal (t/f)

% DATA SETUP
file = uigetfile;
listing = importfile(file);
data = table2array(listing);
% remove top two rows where there are NaNs from column names
time = data(3:end, 5); % time in ps
BRog1 = data(3:end, 2);
BRog2 = data(3:end, 3);
trig = data(3:end, 1);
diode = data(3:end, 4);

% unintegrated raw data
figure(1);
plot(time*(10^-6), interpolate(time, BRog1));
hold on
plot(time*(10^-6), interpolate(time, BRog2));
plot(time*(10^-6), interpolate(time, trig));
plot(time*(10^-6), interpolate(time, diode));
hold off

ax = gca; ax.XAxis.Exponent = 0;
title("All Channels (Raw)");
xlabel("Time (us)"); 
ylabel("Voltage (V)");
legend("BRog1", "BRog2", "Trigger", "Laser Diode x " + ...
    sprintf("%.0e", diodeRawFactor));

%%
% BRog1
figure(2);
subplot(2,2,1);
% raw Rogowski
plot(time*(10^-6), interpolate(time, BRog1));
title("Raw Data");
xlabel("Time (us)");
ylabel("Voltage");

atten_BRog1 = 10.^(dB1/20).*BRog1; % BRog1, accounting for attenuation
subplot(2,2,2);
% smoothed data
xBRog1 = interpolate(time, atten_BRog1);
plot(time*(10^-6), xBRog1);
ax = gca; ax.XAxis.Exponent = 0;
title("Smoothed Rogowski Data");
xlabel("Time (us)");
ylabel("Voltage");

subplot(2,2,3);
% smoothed and integrated
plot(time*(10^-6), cumtrapz(time, xBRog1));

if removeNoise
    hold on
    % returns vector of every value after signal starts
    start1 = find(time >= t1*10^6);
    % finding slope of pre-signal noise
    coeff = polyfit([time(1) time(start1(1))], [xBRog1(1) xBRog1(start1(1))], 1);
    a = coeff(1); % slope of constant line
    b = coeff(2); % y-intercept of constant line
    hold on
    noise = @(t) a*t + b; % noise is some constant line after integration
    
    % smoothed, integrated, w constant slope due to noise subtracted
    % explanation: after integrating the smoothed data, notice that the part of
    % the signal before the trigger (where it's flat and should be 0) has a non
    % zero slope. subtracting that constant slope from the entire waveform
    % should yield a smoothed waveform that has 0 slope before the signal.
    plot(time*(10^-6), cumtrapz(time, xBRog1 - noise(time)));
    hold off
    legend("Integrated", "Noise Removed");
end

ax = gca; ax.XAxis.Exponent = 0;
xlabel("Time (us)");
ylabel("Current");
title("Integrated Rogowski Data");

subplot(2,2,4);
if removeNoise
    plot(time*(10^-6), cumtrapz(time, R1*xBRog1));
    hold on
    plot(time*(10^-6), cumtrapz(time, R1*(xBRog1 - noise(time))));
    hold off
    legend("Unchanged", "Noise Removed");
else
    plot(time*(10^-6), cumtrapz(time, R1*xBRog1));
end

ax = gca; ax.XAxis.Exponent = 0; ax.YAxis.Exponent = 3;
title("Current Through BRog1");
subtitle("Rogowski Coefficient = " + R1)
xlabel("Time (us)");
ylabel("Current (A)");

% BRog2
figure(3);
subplot(2,2,1);
% raw Rogowski
plot(time*(10^-6), interpolate(time, BRog2));
title("Raw Data");
xlabel("Time (us)");
ylabel("Voltage");

atten_BRog2 = 10.^(dB2/20).*BRog2; % BRog2, accounting for attenuation
subplot(2,2,2);
% smoothed data
xBRog2 = interpolate(time, atten_BRog2);
plot(time*(10^-6), xBRog2);
ax = gca; ax.XAxis.Exponent = 0;
title("Smoothed Rogowski Data");
xlabel("Time (us)");
ylabel("Voltage");

subplot(2,2,3);
% smoothed and integrated
plot(time*(10^-6), cumtrapz(time, xBRog2));

if removeNoise
    hold on
    % returns vector of every value after signal starts
    start2 = find(time >= t2*10^6);
    % finding slope of pre-signal noise
    coeff = polyfit([time(1) time(start1(1))], [xBRog2(1) xBRog2(start1(1))], 1);
    a = coeff(1); % slope of constant line
    b = coeff(2); % y-intercept of constant line
    hold on
    noise = @(t) a*t + b; % noise is some constant line after integration
    
    % smoothed, integrated, w constant slope due to noise subtracted
    % explanation: after integrating the smoothed data, notice that the part of
    % the signal before the trigger (where it's flat and should be 0) has a non
    % zero slope. subtracting that constant slope from the entire waveform
    % should yield a smoothed waveform that has 0 slope before the signal.
    plot(time*(10^-6), cumtrapz(time, xBRog2 - noise(time)));
    hold off
    legend("Integrated", "Noise Removed");
end

ax = gca; ax.XAxis.Exponent = 0;
xlabel("Time (us)");
ylabel("Current");
title("Integrated Rogowski Data");

subplot(2,2,4);
if removeNoise
    plot(time*(10^-6), cumtrapz(time, R2*xBRog2));
    hold on
    plot(time*(10^-6), cumtrapz(time, R2*(xBRog2 - noise(time))));
    hold off
    legend("Unchanged", "Noise Removed");
else
    plot(time*(10^-6), cumtrapz(time, R2*xBRog2));
end

ax = gca; ax.XAxis.Exponent = 0; ax.YAxis.Exponent = 3;
title("Current Through BRog2");
subtitle("Rogowski Coefficient = " + R2)
xlabel("Time (us)");
ylabel("Current (A)");

% current from both Rogowskis on top of each other
figure(4);
if removeNoise
    plot(time*(10^-6), cumtrapz(time, R1*(xBRog1 - noise(time))));
    hold on
    plot(time*(10^-6), cumtrapz(time, R2*(xBRog2 - noise(time))));
else
    plot(time*(10^-6), cumtrapz(time, R1*xBRog1));
    hold on
    plot(time*(10^-6), cumtrapz(time, R2*xBRog2));
end

plot(time*(10^-6), interpolate(time, trig));
plot(time*(10^-6), interpolate(time, diode));
hold off
ax = gca; ax.XAxis.Exponent = 0; ax.YAxis.Exponent = 3;
title("All Channels");
xlabel("Time (s)");
ylabel("Current (A)");
legend("BRog1 Current", "BRog2 Current", "Trigger x " + ...
    sprintf("%.0e", trigCurrentFactor), ...
    "Laser Diode x " + sprintf("%.0e", diodeCurrentFactor));

% function to interpolate time and data
function y = interpolate(time, dataY)
    % removing rows in data where there is a NaN
    timeX = time(~isnan(dataY));
    dataYs = dataY(~isnan(dataY));
    % interpolating on unchanged timescale so line stays connected on plot
    y = interp1(timeX, dataYs, time, 'Linear');
    % plot(time, yi)
end

%  listing = IMPORTFILE(FILENAME) reads data from text file FILENAME
    %  for the default selection.  Returns the data as a table.
    %
    %  listing = IMPORTFILE(FILE, DATALINES) reads data for the specified
    %  row interval(s) of text file FILENAME. Specify DATALINES as a
    %  positive scalar integer or a N-by-2 array of positive scalar integers
    %  for dis-contiguous row intervals.
function listing = importfile(filename, dataLines)

    
    % Input handling
    
    % If dataLines is not specified, define defaults
    if nargin < 2
        dataLines = [1, Inf];
    end
    
    % Set up the Import Options and import the data
    opts = delimitedTextImportOptions("NumVariables", 10);
    
    % Specify range and delimiter
    opts.DataLines = dataLines;
    opts.Delimiter = ",";
    
    % Specify column names and types
    opts.VariableNames = ["Var1", "Trigger", "BRog1", "BRog2", "Diode", "Var6", "Var7", "Var8", "Var9", "Time"];
    opts.SelectedVariableNames = ["Trigger", "BRog1", "BRog2", "Diode", "Time"];
    opts.VariableTypes = ["string", "double", "double", "double", "double", "string", "string", "string", "string", "double"];
    
    % Specify file level properties
    opts.ExtraColumnsRule = "ignore";
    opts.EmptyLineRule = "read";
    
    % Specify variable properties
    opts = setvaropts(opts, ["Var1", "Var6", "Var7", "Var8", "Var9"], "WhitespaceRule", "preserve");
    opts = setvaropts(opts, ["Var1", "Var6", "Var7", "Var8", "Var9"], "EmptyFieldRule", "auto");
    
    % Import the data
    listing = readtable(filename, opts);
end