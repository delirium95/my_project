import {
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import type { RecentOrder } from "../api";
import { formatMoney } from "../format";

interface RecentOrdersTableProps {
  orders: RecentOrder[];
}

function shortIdentifier(identifier: string) {
  return `${identifier.slice(0, 10)}…`;
}

export function RecentOrdersTable({ orders }: RecentOrdersTableProps) {
  return (
    <Paper component="section" variant="outlined">
      <Typography component="h2" sx={{ px: 3, pt: 3 }} variant="h6">
        Latest orders
      </Typography>
      <TableContainer>
        <Table aria-label="Latest orders">
          <TableHead>
            <TableRow>
              <TableCell>Order</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Purchased</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders.length > 0 ? (
              orders.map((order) => (
                <TableRow hover key={order.id}>
                  <TableCell title={order.id}>{shortIdentifier(order.id)}</TableCell>
                  <TableCell title={order.customer_id}>{shortIdentifier(order.customer_id)}</TableCell>
                  <TableCell>
                    <Chip color="primary" label={order.status} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>{order.purchased_at}</TableCell>
                  <TableCell align="right">{formatMoney(order.total)}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell align="center" colSpan={5} sx={{ py: 5 }}>
                  No orders yet. Run the Olist seed command to populate the dashboard.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
