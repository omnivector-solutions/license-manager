# License Manager Architecture

## Overview
**License Manager** works in a client/server architecture, where the main components are the **Agent**, the **API** and the **CLI**.

The **License Manager Agent** is the component that syncs the local **Slurm** license counters with the **License Server** data.
It's also responsible for making **Booking** requests to the **License Manager API** when a job is submitted to **Slurm**.

The **License Manager API** provides a **RESTful API** where license usage and **Bookings** are tracked. The **License Manager Agent** uses this **API**
to store the license usage information and to process the **Booking** requests.

The **License Manager CLI** provides an interface for managing license **Configurations** and retrieving usage information for tracked licenses via the **License Manager API**. 


## Architecture
Each component has its own architecture page:

- [License Manager Agent](./agent.md)

- [License Manager API](./api.md)

- [LIcense Manager CLI](./cli.md)