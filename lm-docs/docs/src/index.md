!!! example "An [Omnivector](https://www.omnivector.io/){:target="_blank"} initiative"

    [![omnivector-logo](https://omnivector-public-assets.s3.us-west-2.amazonaws.com/branding/omnivector-logo-text-black-horz.png)](https://www.omnivector.io/){:target="_blank"}


# Welcome to the License Manager documentation!

The License Manager is a license scheduling middleware that operates as an interface between
an HPC cluster and one or more 3rd party license servers. 

It introduces the concept of "license bookings" which are used to provide an alternate source of truth for what licenses are actually available.

It’s responsible for keeping the Slurm license counters in sync with the actual usage from the license servers and preventing jobs from requesting licenses already booked for another job.
