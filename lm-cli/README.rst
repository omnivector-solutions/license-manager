====================
 License Manager CLI
====================

The License Manager CLI is a client to interact with the License Manager API.

The resources that can be interacted with are:

- **Configurations:** information about the license, its features and the location of the license server.
- **Licenses:** Information about license usage and availability.
- **Bookings:** Information about licenses booked for future use.

The Bookings and Licenses information are read only. The Configurations can be edited by users with permission to do so.

Usage
-----

+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli login                                                                | Generate a URL for logging in via browser          |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli show-token                                                           | Print your access token (created after logging in) |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli logout                                                               | Logout and remove your access token                |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli licenses list                                                        | List all licenses                                  |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli licenses list --search <search string>                               | Search licenses with the specified string          |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli licenses list --sort-field <sort field>                              | Sort licenses by the specified field               |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli licenses list --sort-field <sort field> --sort-order ascending       | Sort licenses by the specified order               |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list                                                        | List all bookings                                  |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list --search <search string>                               | Search bookings with the specified string          |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list --sort-field <sort field>                              | Sort bookings by the specified field               |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list --sort-field <sort field> --sort-order ascending       | Sort bookings by the specified order               |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list                                                  | List all configurations                            |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations get-one -- id <configuration id>                      | List the configuration with the specified id       |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list --search <search string>                         | Search configurations with the specified string    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list --sort-field <sort field>                        | Sort configurations by the specified field         |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list --sort-field <sort field> --sort-order ascending | Sort configurations by the specified order         |
+-----------------------------------------------------------------------------+----------------------------------------------------+

License
-------
* `MIT <LICENSE>`_


Copyright
---------
* Copyright (c) 2022 OmniVector Solutions <info@omnivector.solutions>
