import { NavLink } from "@/components/NavLink";
import { Link } from "react-router-dom";
import logoMark from "@/assets/logo.svg";

const Navigation = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/90 backdrop-blur-xl shadow-[0_6px_30px_rgba(20,40,20,0.08)]">
      <div className="flex h-24 w-full items-center justify-between px-10">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 shadow-[0_14px_34px_rgba(34,197,94,0.16)]">
            <img
              src={logoMark}
              alt="Cropter logo"
              className="h-10 w-10"
            />
          </div>
          <div>
            <span className="text-3xl font-semibold tracking-tight text-foreground">
              Cropter
            </span>
            <span className="block text-xs uppercase tracking-[0.48em] text-muted-foreground mt-1">
              AI Monitoring
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
            <NavLink
            to="/"
            className="relative overflow-hidden rounded-full px-6 py-2.5 text-base font-medium text-muted-foreground transition-all duration-300 hover:text-foreground hover:bg-secondary/60 after:absolute after:inset-x-6 after:bottom-[7px] after:h-[2px] after:origin-left after:scale-x-0 after:bg-primary after:transition-transform after:duration-300 hover:after:scale-x-100"
            activeClassName="!text-primary !bg-primary/10 !shadow-[0_0_0_1px_rgba(34,197,94,0.35)] !after:scale-x-100"
          >
            Home
          </NavLink>
          <NavLink
            to="/features"
            className="relative overflow-hidden rounded-full px-6 py-2.5 text-base font-medium text-muted-foreground transition-all duration-300 hover:text-foreground hover:bg-secondary/60 after:absolute after:inset-x-6 after:bottom-[7px] after:h-[2px] after:origin-left after:scale-x-0 after:bg-primary after:transition-transform after:duration-300 hover:after:scale-x-100"
            activeClassName="!text-primary !bg-primary/10 !shadow-[0_0_0_1px_rgba(34,197,94,0.35)] !after:scale-x-100"
          >
            Features
          </NavLink>
          <NavLink
              to="/farm-mapping"
              className="relative overflow-hidden rounded-full px-6 py-2.5 text-base font-medium text-muted-foreground transition-all duration-300 hover:text-foreground hover:bg-secondary/60 after:absolute after:inset-x-6 after:bottom-[7px] after:h-[2px] after:origin-left after:scale-x-0 after:bg-primary after:transition-transform after:duration-300 hover:after:scale-x-100"
              activeClassName="!text-primary !bg-primary/10 !shadow-[0_0_0_1px_rgba(34,197,94,0.35)] !after:scale-x-100"
            >
              Farm Map
            </NavLink>
            <NavLink
            to="/mission-control"
            className="relative overflow-hidden rounded-full px-6 py-2.5 text-base font-medium text-muted-foreground transition-all duration-300 hover:text-foreground hover:bg-secondary/60 after:absolute after:inset-x-6 after:bottom-[7px] after:h-[2px] after:origin-left after:scale-x-0 after:bg-primary after:transition-transform after:duration-300 hover:after:scale-x-100"
            activeClassName="!text-primary !bg-primary/10 !shadow-[0_0_0_1px_rgba(34,197,94,0.35)] !after:scale-x-100"
          >
            Mission
          </NavLink>
          <NavLink
              to="/my-farm"
              className="relative overflow-hidden rounded-full px-6 py-2.5 text-base font-medium text-muted-foreground transition-all duration-300 hover:text-foreground hover:bg-secondary/60 after:absolute after:inset-x-6 after:bottom-[7px] after:h-[2px] after:origin-left after:scale-x-0 after:bg-primary after:transition-transform after:duration-300 hover:after:scale-x-100"
              activeClassName="!text-primary !bg-primary/10 !shadow-[0_0_0_1px_rgba(34,197,94,0.35)] !after:scale-x-100"
            >
              Results
            </NavLink>
          <Link
            to="/mission-control"
            className="ml-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-emerald-500 px-7 py-3 text-base font-semibold text-primary-foreground shadow-[0_16px_40px_rgba(34,197,94,0.25)] transition-transform hover:-translate-y-0.5 hover:shadow-[0_20px_50px_rgba(34,197,94,0.32)]"
          >
            Launch Mission
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
