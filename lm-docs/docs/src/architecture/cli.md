## License Manager CLI
The **License Manager CLI** is a client to interact with the **License Manager API**.

It can be used to add new configurations to the API and to check the usage information for each tracked license.

The **Jobs** and **Bookings** are read only. The remaining resources can be edited by users with permission to do so.

### Global commands
| **Command** | **Description** |
| ----------- | ----------------|
| lm-cli login | Generate a URL for logging in via browser |
| lm-cli show-token | Print your access token (created after logging in) |
| lm-cli logout | Logout and remove your access token |

### Configuration commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli configurations list | List all configurations |
| lm-cli configurations list<br>--search **<search string\>** | Search configurations with the specified string |
| lm-cli configurations list<br>--sort-field **<sort field\>** | Sort configurations by the specified field |
| lm-cli configurations list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort configurations by the specified order |
| lm-cli configurations get-one<br>--id **<configuration id\>** | List the configuration with the specified id |
| lm-cli configurations create<br>--name **<configuration name\>**<br>--cluster-client-id **<OIDC client_id of the cluster where the configuration applies\>**<br>--grace-time **<grace time in seconds\>**<br>--license-server-type **<License Server type\>** | Create a new configuration |
| lm-cli configurations delete<br>--id **<id to delete\>** | Delete the configuration with the specified id |

### License server commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli license-servers list | List all License Servers |
| lm-cli license-servers list<br>--search **<search string\>** | Search License Servers with the specified string |
| lm-cli license-servers list<br>--sort-field **<sort field\>** | Sort License Servers by the specified field |
| lm-cli license-servers list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort License Servers by the specified order |
| lm-cli license-servers get-one<br>--id **<License Server id\>** | List the License Server with the specified id |
| lm-cli license-servers create<br>--config-id **<id of the configuration to add the License Server\>**<br>--host **<hostname of the License Server\>**<br>--port **<port of the License Server\>** | Create a new License Server |
| lm-cli license-servers delete<br>--id **<id to delete\>** | Delete the License Server with the specified id    |

### Product commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli products list | List all products |
| lm-cli products list<br>--search **<search string\>** | Search products with the specified string |
| lm-cli products list<br>--sort-field **<sort field\>** | Sort products by the specified field |
| lm-cli products list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort products by the specified order |
| lm-cli products get-one<br>--id **<product id\>** | List the product with the specified id |
| lm-cli products create<br>--name **<product name\>** | Create a new product |
| lm-cli products delete<br>--id **<id to delete\>** | Delete the product with the specified id |

### Feature commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli features list | List all features |
| lm-cli features list<br>--search **<search string\>** | Search features with the specified string |
| lm-cli features list<br>--sort-field **<sort field\>** | Sort features by the specified field |
| lm-cli features list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort features by the specified order |
| lm-cli features get-one<br>--id **<feature id\>** | List the feature with the specified id |
| lm-cli features create<br>--name **<feature name\>**<br>--product-id **<id of the product of the license\>**<br>--config-id **<id of the configuration of the license\>**<br>--reserved **<how many licenses should be reserved for desktop environments\>** | Create a new feature |
| lm-cli features delete<br>--id **<id to delete\>** | Delete the feature with the specified id |

### Job commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli jobs list | List all jobs |
| lm-cli jobs list<br>--search **<search string\>** | Search jobs with the specified string |
| lm-cli jobs list<br>--sort-field **<sort field\>** | Sort jobs by the specified field |
| lm-cli jobs list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort jobs by the specified order |

### Booking commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli bookings list | List all bookings |
| lm-cli bookings list<br>--search **<search string\>** | Search bookings with the specified string |
| lm-cli bookings list<br>--sort-field **<sort field\>** | Sort bookings by the specified field |
| lm-cli bookings list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>**| Sort bookings by the specified order |


## Reference
The [reference](../reference/cli.md) page contains more information about the commands available.