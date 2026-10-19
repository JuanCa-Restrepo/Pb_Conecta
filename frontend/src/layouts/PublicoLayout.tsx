import { AppBar, Box, Button, Container, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, Outlet } from "react-router-dom";

export function PublicoLayout() {
  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography component={RouterLink} to="/" variant="h6" sx={{ flexGrow: 1, fontWeight: 700, color: "inherit", textDecoration: "none" }}>
            PB Conecta
          </Typography>
          <Button color="inherit" component={RouterLink} to="/empresas">Empresas aliadas</Button>
          <Button color="inherit" component={RouterLink} to="/iniciar-sesion">Iniciar sesión</Button>
        </Toolbar>
      </AppBar>
      <Container component="main" maxWidth="lg" sx={{ py: { xs: 3, md: 5 }, flexGrow: 1 }}>
        <Outlet />
      </Container>
      <Box component="footer" sx={{ py: 2, textAlign: "center", color: "text.secondary", fontSize: 13 }}>
        Institución Universitaria Pascual Bravo · Oficina de prácticas
      </Box>
    </Box>
  );
}
