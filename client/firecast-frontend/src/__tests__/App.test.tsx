// @Gomurmamma, youngdo@oregonstate.edu
// Example test from
// https://medium.com/@nedopaka/setup-a-react-vite-project-with-typescript-prettier-vitest-2024-9bb6e919ac8f
// 1/27/2025

import { describe, it, expect, test } from "vitest";
import { render } from "@testing-library/react";
import App from "../App";

test("demo", () => {
  expect(true).toBe(true);
});

describe("render", () => {
  it("renders the main page", () => {
    render(<App />);
    expect(true).toBeTruthy();
  });
});
