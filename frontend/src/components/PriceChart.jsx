import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";


function formatPrice(value) {
  return `₹${Number(
    value
  ).toLocaleString(
    "en-IN"
  )}`;
}


function formatDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
    }
  );
}


function PriceChart({
  history = [],
}) {

  const data =
    history.map(
      (item) => ({
        label: formatDate(
          item.date
        ),
        price: Number(
          item.price
        ),
      })
    );


  if (data.length === 0) {

    return (
      <div className="empty-state">

        <h3>
          No price history yet
        </h3>

        <p>
          A successful scrape will
          create the first record.
        </p>

      </div>
    );
  }


  return (
    <div className="chart-card">

      <div className="price-chart">

        <ResponsiveContainer
          width="100%"
          height="100%"
        >

          <LineChart
            data={data}
            margin={{
              top: 15,
              right: 20,
              left: 10,
              bottom: 5,
            }}
          >

            <CartesianGrid
              strokeDasharray="3 3"
            />

            <XAxis
              dataKey="label"
            />

            <YAxis
              tickFormatter={
                formatPrice
              }
            />

            <Tooltip
              formatter={(
                value
              ) => [
                formatPrice(
                  value
                ),
                "Price",
              ]}
            />

            <Line
              type="monotone"
              dataKey="price"
              stroke="var(--dark)"
              strokeWidth={2}
              dot={{
                r: 3,
              }}
            />

          </LineChart>

        </ResponsiveContainer>

      </div>

    </div>
  );
}


export default PriceChart;