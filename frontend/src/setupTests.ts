// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";

// Mock the axios module
jest.mock("axios", () => ({
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  patch: jest.fn(() => Promise.resolve({ data: {} })),
}));

// Mock the localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

// Mock the matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock the ResizeObserver
(globalThis as any).ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock Recharts components for testing
jest.mock("recharts", () => {
  const React = require("react");
  return {
    LineChart: ({ children, ...props }: any) =>
      React.createElement(
        "div",
        {
          className: "recharts-line-chart",
          "data-testid": "line-chart",
          ...props,
        },
        [
          React.createElement(
            "div",
            {
              className: "recharts-line",
              key: "line",
            },
            children
          ),
        ]
      ),
    AreaChart: ({ children, ...props }: any) =>
      React.createElement(
        "div",
        {
          className: "recharts-area-chart",
          "data-testid": "area-chart",
          ...props,
        },
        [
          React.createElement("div", {
            className: "recharts-area",
            key: "area",
          }),
          children,
        ]
      ),
    BarChart: ({ children, ...props }: any) =>
      React.createElement(
        "div",
        {
          className: "recharts-bar-chart",
          "data-testid": "bar-chart",
          ...props,
        },
        [
          React.createElement("div", {
            className: "recharts-bar",
            key: "bar",
          }),
          children,
        ]
      ),
    Line: ({ stroke, ...props }: any) =>
      React.createElement("div", {
        className: "recharts-line-curve",
        stroke,
        ...props,
      }),
    Area: ({ stroke, fill, ...props }: any) =>
      React.createElement("div", {
        className: "recharts-area",
        stroke,
        fill,
        ...props,
      }),
    Bar: ({ fill, ...props }: any) =>
      React.createElement("div", {
        className: "recharts-bar",
        fill,
        ...props,
      }),
    XAxis: (props: any) =>
      React.createElement("div", {
        className: "recharts-xaxis",
        ...props,
      }),
    YAxis: (props: any) =>
      React.createElement("div", {
        className: "recharts-yaxis",
        ...props,
      }),
    CartesianGrid: (props: any) =>
      React.createElement("div", {
        className: "recharts-cartesian-grid",
        ...props,
      }),
    Tooltip: (props: any) =>
      React.createElement("div", {
        className: "recharts-tooltip",
        ...props,
      }),
    Legend: (props: any) =>
      React.createElement("div", {
        className: "recharts-legend-wrapper",
        ...props,
      }),
    ResponsiveContainer: ({ children, ...props }: any) =>
      React.createElement(
        "div",
        {
          className: "recharts-responsive-container",
          ...props,
        },
        children
      ),
  };
});
