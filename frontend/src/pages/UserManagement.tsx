import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tooltip,
} from "@mui/material";
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import axios from "axios";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/Toast";
import ErrorDisplay from "../components/ErrorDisplay";
import { parseError, getValidationErrors } from "../utils/errorHandling";

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    email: "",
    full_name: "",
    role: "",
    is_active: true,
    password: "",
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const { user } = useAuth();
  const toast = useToast();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get("/auth/admin/users");
      setUsers(response.data);
    } catch (err) {
      const parsedError = parseError(err);
      setError(parsedError.message);
      toast.showError("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (userToEdit: User) => {
    setSelectedUser(userToEdit);
    setEditForm({
      email: userToEdit.email,
      full_name: userToEdit.full_name || "",
      role: userToEdit.role,
      is_active: userToEdit.is_active,
      password: "",
    });
    setFieldErrors({});
    setEditDialogOpen(true);
  };

  const handleSaveUser = async () => {
    if (!selectedUser) return;

    try {
      setFieldErrors({});
      const updateData: any = {
        email: editForm.email,
        full_name: editForm.full_name || null,
        role: editForm.role,
        is_active: editForm.is_active,
      };

      if (editForm.password) {
        updateData.password = editForm.password;
      }

      await axios.patch(`/auth/admin/users/${selectedUser.id}`, updateData);

      toast.showSuccess("User updated successfully");
      setEditDialogOpen(false);
      fetchUsers();
    } catch (err) {
      const parsedError = parseError(err);
      const validationErrors = getValidationErrors(err);

      if (Object.keys(validationErrors).length > 0) {
        setFieldErrors(validationErrors);
      } else {
        toast.showError(parsedError.message);
      }
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    try {
      await axios.delete(`/auth/admin/users/${selectedUser.id}`);
      toast.showSuccess("User deleted successfully");
      setDeleteDialogOpen(false);
      fetchUsers();
    } catch (err) {
      const parsedError = parseError(err);
      toast.showError(parsedError.message);
    }
  };

  const handleToggleUserStatus = async (userToToggle: User) => {
    try {
      const action = userToToggle.is_active ? "deactivate" : "activate";
      await axios.post(`/auth/admin/users/${userToToggle.id}/${action}`);

      toast.showSuccess(
        `User ${userToToggle.is_active ? "deactivated" : "activated"} successfully`
      );
      fetchUsers();
    } catch (err) {
      const parsedError = parseError(err);
      toast.showError(parsedError.message);
    }
  };

  const getRoleColor = (role: string) => {
    return role === "admin" ? "error" : "default";
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive ? "success" : "default";
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Typography>Loading users...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          User Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage user accounts, roles, and permissions
        </Typography>
      </Box>

      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={() => setError(null)}
          variant="outlined"
        />
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Full Name</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((userRow) => (
              <TableRow key={userRow.id}>
                <TableCell>{userRow.username}</TableCell>
                <TableCell>{userRow.email}</TableCell>
                <TableCell>{userRow.full_name || "-"}</TableCell>
                <TableCell>
                  <Chip
                    label={userRow.role}
                    color={getRoleColor(userRow.role)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={userRow.is_active ? "Active" : "Inactive"}
                    color={getStatusColor(userRow.is_active)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(userRow.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <Tooltip title="Edit User">
                    <IconButton
                      size="small"
                      onClick={() => handleEditUser(userRow)}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip
                    title={userRow.is_active ? "Deactivate" : "Activate"}
                  >
                    <span>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleUserStatus(userRow)}
                        disabled={userRow.id === user?.id}
                      >
                        {userRow.is_active ? (
                          <BlockIcon />
                        ) : (
                          <CheckCircleIcon />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title="Delete User">
                    <span>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedUser(userRow);
                          setDeleteDialogOpen(true);
                        }}
                        disabled={userRow.id === user?.id}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit User Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <TextField
            margin="normal"
            fullWidth
            label="Email"
            value={editForm.email}
            onChange={(e) =>
              setEditForm({ ...editForm, email: e.target.value })
            }
            error={!!fieldErrors.email}
            helperText={fieldErrors.email}
          />
          <TextField
            margin="normal"
            fullWidth
            label="Full Name"
            value={editForm.full_name}
            onChange={(e) =>
              setEditForm({ ...editForm, full_name: e.target.value })
            }
            error={!!fieldErrors.full_name}
            helperText={fieldErrors.full_name}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Role</InputLabel>
            <Select
              value={editForm.role}
              onChange={(e) =>
                setEditForm({ ...editForm, role: e.target.value })
              }
              disabled={selectedUser?.id === user?.id}
            >
              <MenuItem value="user">User</MenuItem>
              <MenuItem value="admin">Admin</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={editForm.is_active}
                onChange={(e) =>
                  setEditForm({ ...editForm, is_active: e.target.checked })
                }
                disabled={selectedUser?.id === user?.id}
              />
            }
            label="Active"
          />
          <TextField
            margin="normal"
            fullWidth
            label="New Password (optional)"
            type="password"
            value={editForm.password}
            onChange={(e) =>
              setEditForm({ ...editForm, password: e.target.value })
            }
            error={!!fieldErrors.password}
            helperText={
              fieldErrors.password || "Leave blank to keep current password"
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveUser} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user &quot;{selectedUser?.username}
            &quot;? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteUser} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagement;
