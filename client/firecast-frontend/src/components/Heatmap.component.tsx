import React, { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import useSWR from "swr";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { MdEmergency } from "react-icons/md";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

// Define a fetcher function
const fetcher = (url) => fetch(url).then((res) => res.json());

// Custom useInterval hook
// TODO: Need e2e test with backend API
const useInterval = (callback, delay) => {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    const tick = () => {
      savedCallback.current();
    };
    if (delay !== null) {
      let id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
};

const Heatmap: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const [map, setMap] = useState<mapboxgl.Map | null>(null);
  const [time, setTime] = useState<number>(
    Math.floor(new Date(new Date()).getTime())
  ); // Current time (e.g., Unix timestamp)
  const [timeRange, setTimeRange] = useState<[number, number]>([0, 0]); // Min and max time
  const [tempInt, setTempInt] = useState<number>(30); // minutes
  const [updateInterval, setUpdateInterval] = useState<number>(30); // 30 minutes

  let dateObj = new Date();
  let year = dateObj.getFullYear();
  let month = String(dateObj.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed
  let day = String(dateObj.getDate()).padStart(2, "0");
  // Format as yyyy-mm-dd
  let formattedDate = `${year}-${month}-${day}`;
  const [startDate, setStartDate] = useState(formattedDate);

  // const endDateObj = new Date();
  // endDateObj.setDate(endDateObj.getDate() + 7);
  // let endYear = dateObj.getFullYear();
  // let endMonth = String(dateObj.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed
  // let endDay = String(dateObj.getDate()).padStart(2, "0");
  // Format as yyyy-mm-dd
  let endFormattedDate = "2025-03-16";

  const [endDate, setEndDate] = useState(endFormattedDate);

  const constructUrl = (baseUrl, params) => {
    const queryString = new URLSearchParams(params).toString();
    return `${baseUrl}?${queryString}`;
  };

  const params = {
    start_date: startDate,
    end_date: endDate,
  };

  const url = constructUrl("http://127.0.0.1:8000/api/heatmap", params);

  // Use the useSWR hook to fetch data
  // TODO: request data on click with /heatmap
  const { data, error, mutate } = useSWR(url, fetcher, {
    onSuccess: (data) => {
      const times = data.features.map((f) =>
        new Date(f.properties.time).getTime()
      );
      setTimeRange([Math.min(...times), Math.max(...times)]);
      // setTime(Math.min(...times));
    },
  });

  // Use the custom useInterval hook to re-fetch data periodically
  useInterval(
    () => {
      mutate();
    },
    updateInterval * 60 * 1000 // Time conversion needed for input slider
  );

  // Make requests to /api/train and /api/predict on component mount
  useEffect(() => {
    const trainModel = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/train/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });
        const data = await response.json();
        console.log("Training response:", data);
      } catch (err) {
        console.error("Training error:", err);
      }
    };

    const predictModel = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/predict/", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        const data = await response.json();
      } catch (err) {
        console.error("Predict error:", err);
      }
    };

    trainModel();
    predictModel();
  }, []);

  // Render the Map
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v11",
      center: [-80.75, 35.2464],
      zoom: 8,
      maxZoom: 21,
      zoomSnap: 0.5,
    });

    // http://127.0.0.1:8000/heatmap POST YYYY-MM-DD str
    // update this so request is made on submission
    // on load > train, and predict requests then submit for heatmap w/ params
    map.on("load", () => {
      map.addSource("callVolume", {
        type: "geojson",
        data: "http://127.0.0.1:8000/api/heatmap",
        generateId: true,
      });

      // Layer styles can change
      map.addLayer({
        id: "call-volume-heat",
        type: "heatmap",
        source: "callVolume",

        paint: {
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["get", "volume"],
            0,
            0,
            15, // Sets the high end of the volume heatmap gradient
            1,
          ],
          "heatmap-intensity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            0,
            1,
            9,
            3,
          ],
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(33,102,172,0)", // Transparent at low density
            0.2,
            "rgb(103,169,207)", // Light blue
            0.4,
            "rgb(209,229,240)", // Very light blue
            0.6,
            "rgb(253,219,199)", // Light orange
            0.8,
            "rgb(239,138,98)", // Orange
            1,
            "rgb(178,24,43)", // Dark red at high density
          ],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 2, 9, 20],
          "heatmap-opacity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            2,
            0.4,
            9,
            0.9,
            22,
            0.95,
          ],
        },
      });

      setMap(map);
    });

    return () => map.remove();
  }, []);

  // Update the heatmap layer filter when `time` changes
  useEffect(() => {
    if (!map) return;

    const endTime = time + 24 * 60 * 60 * 1000; // 24 hours from now
    // const endTime = time + 3 * 24 * 60 * 60 * 1000; // 3 days later

    map.setFilter("call-volume-heat", [
      "all",
      [">=", ["to-number", ["get", "time"]], time],
      ["<=", ["to-number", ["get", "time"]], endTime],
    ]);
  }, [time, map]);

  const handleTimeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTime(Number(event.target.value));
  };

  const handleDateChange = (date) => {
    setTime(date.getMilliseconds()); // convert the calendar date into unix timestamp for filtering
  };

  const convertTimeStampToDate = (milliseconds: number) => {
    // Convert to a Date object (multiply by 1000 to convert seconds to milliseconds)
    const dateObj = new Date(milliseconds);

    // Extract year, month, and day
    const year = dateObj.getFullYear();

    const month = String(dateObj.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed

    const day = String(dateObj.getDate()).padStart(2, "0");

    // Format as yyyy-mm-dd
    const formattedDate = `${year}-${month}-${day}`;

    return formattedDate;
  };

  const handleIntervalChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTempInt(Number(event.target.value));
  };

  const submitIntervalChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    //console.log("click me");
    setTempInt(Number(tempInt));
    setUpdateInterval(Number(tempInt));
  };

  // Aggregate call volumes by cluster
  const aggregateCallVolumes = () => {
    if (!data) return {};

    const clusters = {};
    data.features.forEach((feature) => {
      const clusterId = feature.properties.cluster_id;
      const volume = feature.properties.volume;
      if (!clusters[clusterId]) {
        clusters[clusterId] = 0;
      }
      clusters[clusterId] += volume;
    });

    return clusters;
  };

  const clusters = aggregateCallVolumes();
  const totalCallVolume = Object.values(clusters).reduce(
    (sum, volume) => sum + volume,
    0
  );

  return (
    <section className="h-screen" style={{ maxWidth: "75%", margin: "0 auto" }}>
      <figcaption
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          backgroundColor: "Gray",
        }}
      >
        <h3>Demand Forecast</h3>
        <p
          style={{
            textTransform: "uppercase",
            fontSize: "12px",
          }}
        >
          Charlotte, NC Map
        </p>
        <ul style={{ display: "block", padding: "5px" }}>
          <li
            style={{
              display: "flex",
              flexDirection: "row",
              alignItems: "center",
            }}
          >
            <MdEmergency
              title="Expected Call Demand"
              style={{ marginRight: "5px" }}
            />{" "}
            <div
              style={{ width: "10px", height: "10px", backgroundColor: "red" }}
            ></div>
            <div
              style={{
                width: "10px",
                height: "10px",
                backgroundColor: "orange",
              }}
            ></div>
            <div
              style={{
                width: "10px",
                height: "10px",
                backgroundColor: "yellow",
              }}
            ></div>
            <div
              style={{
                width: "10px",
                height: "10px",
                backgroundColor: "white",
              }}
            ></div>
          </li>
        </ul>
      </figcaption>
      <figure ref={mapContainer} style={{ width: "100%", height: "50vh" }} />

      <article>
        <input
          type="range"
          min={timeRange[0] || 0}
          max={timeRange[1] || 0}
          step={1000 * 60 * 60 * 24} // Step by day
          value={time}
          onChange={handleTimeChange}
          className="slider" /* Shadcn slider style. Feel free to remove or restyle */
        />
        <p>
          {" "}
          Displaying Forecast for:{" "}
          {time
            ? new Date(time).toLocaleString().slice(0, -12)
            : "no time data"}
        </p>
        <div
        // style={{
        //   display: "flex",
        //   flexDirection: "row",
        //   alignItems: "center",
        // }}
        >
          <div style={{ margin: "10px" }}>
            <p>start date:</p>
            <DatePicker selected={startDate} dateFormat="yyyy-MM-dd" />
          </div>
          <div style={{ margin: "10px" }}>
            <p>end date:</p>
            <DatePicker selected={endDate} dateFormat="yyyy-MM-dd" />
          </div>
          <label
            htmlFor="refreshInt"
            style={{ width: "250px", height: "min-content" }}
          >
            Current Refresh Rate: {updateInterval} min. Minimum time is 1 minute
          </label>

          <Input
            type="number"
            id="refreshInt"
            value={tempInt}
            onChange={handleIntervalChange}
            min="1" // Should probably be the min time it takes to train the model
            style={{ height: "min-content" }}
          />
          <Button onClick={submitIntervalChange}>Update</Button>
        </div>
      </article>
      {/* Table to display call volumes by cluster and percentages */}
      <table
        style={{
          borderCollapse: "collapse",
          marginTop: "10px",
          marginBottom: "30px",
        }}
      >
        <thead>
          <tr>
            <th style={{ border: "1px solid #ddd", padding: "8px" }}>
              Cluster ID
            </th>
            <th style={{ border: "1px solid #ddd", padding: "8px" }}>
              Call Volume
            </th>
            <th style={{ border: "1px solid #ddd", padding: "8px" }}>
              Percentage of Total
            </th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(clusters).map(([clusterId, volume]) => {
            const percentage = ((volume / totalCallVolume) * 100).toFixed(2); // Calculate percentage
            return (
              <tr key={clusterId}>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {clusterId}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {volume}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {percentage}%
                </td>
              </tr>
            );
          })}
          <tr>
            <td
              style={{
                border: "1px solid #ddd",
                padding: "8px",
                fontWeight: "bold",
              }}
            >
              Total
            </td>
            <td
              style={{
                border: "1px solid #ddd",
                padding: "8px",
                fontWeight: "bold",
              }}
            >
              {totalCallVolume}
            </td>
            <td
              style={{
                border: "1px solid #ddd",
                padding: "8px",
                fontWeight: "bold",
              }}
            >
              100%
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
};

export default Heatmap;
