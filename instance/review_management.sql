-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 28, 2024 at 08:32 AM
-- Server version: 10.4.27-MariaDB
-- PHP Version: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `review_management`
--

-- --------------------------------------------------------

--
-- Table structure for table `review`
--

CREATE TABLE `review` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `rating` int(11) NOT NULL,
  `comment` text NOT NULL,
  `date_submitted` datetime DEFAULT NULL,
  `user_id` varchar(36) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `review`
--

INSERT INTO `review` (`id`, `name`, `email`, `rating`, `comment`, `date_submitted`, `user_id`) VALUES
(1, 'pName', 'hasibur959@gmail.com', 3, 'this is test', '2024-08-23 17:34:47', 'b65eca74-a13e-4ec4-af6f-a7e02aaee7e0'),
(2, 'abbas ', 'hasibur959@gmail.com', 3, 'This is 2nd test', '2024-08-23 17:41:29', '58f9dd32-5988-4bba-83ad-71b83e90b6bc'),
(3, 'pName', 'hasibur959@gmail.com', 3, 'This is test', '2024-08-26 13:30:08', '58f9dd32-5988-4bba-83ad-71b83e90b6bc'),
(4, 'Howcanwehelp', 'hasibur959@gmail.com', 3, 'cfqwe', '2024-08-27 11:52:45', '58f9dd32-5988-4bba-83ad-71b83e90b6bc'),
(5, 'message', 'hasibur+1959@gmail.com', 3, 'sdvsw', '2024-08-27 13:49:51', '58f9dd32-5988-4bba-83ad-71b83e90b6bc'),
(6, 'Howcanwehelp', 'hasibur959+1@gmail.com', 3, 'adeqwdf', '2024-08-27 13:51:58', 'b65eca74-a13e-4ec4-af6f-a7e02aaee7e0'),
(7, 'message', 'abbas@gmail.com', 2, 'few', '2024-08-27 17:08:39', 'b65eca74-a13e-4ec4-af6f-a7e02aaee7e0');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` varchar(36) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL,
  `active` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `username`, `password`, `role`, `active`) VALUES
('138cb63e-6832-4b31-b3f4-86ec7e8e3109', 'madhu', 'scrypt:32768:8:1$yQLkmLIDrWw9qe2N$d12da7b2c7526bc49209685f997f414afa51d4bdecaa88372d6122e2a2c264e29383ae96570208dfe496fee022db0085ef32dccd2ff331472be2e101377dfe04', 'subscriber', 1),
('58f9dd32-5988-4bba-83ad-71b83e90b6bc', 'abir', 'scrypt:32768:8:1$vIYnzGvGF0g816DK$e1f08c03b15a218852a19fd6786d097b81c2b0c8606b08402c55969d42808d4d0c6b3620e5dbe914b6d65ccd85a10a4552a22ef3537022f87cb545f0e9d970a7', 'subscriber', 1),
('85f6ae8e-4304-4774-aadd-ced87d9e6779', 'abbus', 'scrypt:32768:8:1$Cv1xl4aAQY63SFVw$1b100ece04df9aa6efdbf405ecfd0eb2ee9b06a626cb3633cc25ed1e2a73322e5eb38ea57f66858900e782673a7d7baccbc01223fec0bd98d0435657a88f8f88', 'subscriber', 1),
('a4b5e617-c55d-4b4d-9b98-df53b3e6cb1f', 'ank', 'scrypt:32768:8:1$OTuDVBgNnsxrRbc0$4c8ee4efa5c3fd31f8defa748c272420c97250d349ddd984337bc35d7246b545c2f7128374ca8ab9627a2b0ee0be370ab55c290e878f768d0483812cc01a3b0c', 'subscriber', 1),
('b65eca74-a13e-4ec4-af6f-a7e02aaee7e0', 'abc', 'scrypt:32768:8:1$d5No1lQES8N3SJas$775658c5f8403496b1c44f6ec288710bb8dacd29c72a3944850a5ac9b0fef4bb6f2d08bc7d6dce9955e78773cdf7484635587a29c70468a7349cf4d7c3fd5306', 'subscriber', 1),
('c57e3963-4a30-4d2b-b2d6-324028688c51', 'hasibur959@gmail.com', 'scrypt:32768:8:1$lTjfQsdbOS582HeP$2686ab6360da9239ec8837c8e38bbd96bd80af71531fbef2ec15899f129fd6e9523e0297ccb800e370d55745803c3164987b4299d14f7ee062fafe14d25f8d46', 'administrator', 1);

-- --------------------------------------------------------

--
-- Table structure for table `user_meta`
--

CREATE TABLE `user_meta` (
  `id` int(11) NOT NULL,
  `company_name` varchar(150) DEFAULT NULL,
  `phone_number` varchar(15) DEFAULT NULL,
  `company_address` varchar(250) DEFAULT NULL,
  `google_review_url` text DEFAULT NULL,
  `user_id` varchar(36) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `user_meta`
--

INSERT INTO `user_meta` (`id`, `company_name`, `phone_number`, `company_address`, `google_review_url`, `user_id`) VALUES
(1, 'Techievolve', '0123654789', 'Sec V, Kolkata, 700096', 'https://www.google.com/search?q=techievolve&amp;rlz=1C1CHBF_enIN1100IN1100&amp;oq=techievolve&amp;gs_lcrp=EgZjaHJvbWUqCggAEAAY4wIYgAQyCggAEAAY4wIYgAQyBggBEEUYPDIGCAIQRRg8Mg0IAxAuGK8BGMcBGIAEMgYIBBBFGDwyBggFEEUYPDIGCAYQRRg8MgYIBxBFGDzSAQg1NzI2ajBqN6gCCLACA#lrd=0x3a0275ae35cc0001:0xaa91c47c69349a06,3,,,,', 'c57e3963-4a30-4d2b-b2d6-324028688c51'),
(2, 'Techievolve', '0123654789', 'Sec V, Kolkata, 700096', 'https://www.google.com/search?q=techievolve&amp;rlz=1C1CHBF_enIN1100IN1100&amp;oq=techievolve&amp;gs_lcrp=EgZjaHJvbWUqCggAEAAY4wIYgAQyCggAEAAY4wIYgAQyBggBEEUYPDIGCAIQRRg8Mg0IAxAuGK8BGMcBGIAEMgYIBBBFGDwyBggFEEUYPDIGCAYQRRg8MgYIBxBFGDzSAQg1NzI2ajBqN6gCCLACA#lrd=0x3a0275ae35cc0001:0xaa91c47c69349a06,3,,,,', 'b65eca74-a13e-4ec4-af6f-a7e02aaee7e0'),
(3, 'Techievolve 2', '0123654789', 'Sec V, Kolkata, 700096', 'https://www.google.com/search?q=techievolve&amp;rlz=1C1CHBF_enIN1100IN1100&amp;oq=techievolve&amp;gs_lcrp=EgZjaHJvbWUqCggAEAAY4wIYgAQyCggAEAAY4wIYgAQyBggBEEUYPDIGCAIQRRg8Mg0IAxAuGK8BGMcBGIAEMgYIBBBFGDwyBggFEEUYPDIGCAYQRRg8MgYIBxBFGDzSAQg1NzI2ajBqN6gCCLACA#lrd=0x3a0275ae35cc0001:0xaa91c47c69349a06,3,,,,', '58f9dd32-5988-4bba-83ad-71b83e90b6bc'),
(4, 'Techievolve', '0123654789', 'Sec V, Kolkata, 700096', 'https://www.google.com/search?q=techievolve&amp;rlz=1C1CHBF_enIN1100IN1100&amp;oq=techievolve&amp;gs_lcrp=EgZjaHJvbWUqCggAEAAY4wIYgAQyCggAEAAY4wIYgAQyBggBEEUYPDIGCAIQRRg8Mg0IAxAuGK8BGMcBGIAEMgYIBBBFGDwyBggFEEUYPDIGCAYQRRg8MgYIBxBFGDzSAQg1NzI2ajBqN6gCCLACA#lrd=0x3a0275ae35cc0001:0xaa91c47c69349a06,3,,,,', '138cb63e-6832-4b31-b3f4-86ec7e8e3109'),
(5, '', '', '', NULL, 'a4b5e617-c55d-4b4d-9b98-df53b3e6cb1f'),
(6, '', '', '', NULL, '85f6ae8e-4304-4774-aadd-ced87d9e6779');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `review`
--
ALTER TABLE `review`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `user_meta`
--
ALTER TABLE `user_meta`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `review`
--
ALTER TABLE `review`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `user_meta`
--
ALTER TABLE `user_meta`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `review`
--
ALTER TABLE `review`
  ADD CONSTRAINT `review_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);

--
-- Constraints for table `user_meta`
--
ALTER TABLE `user_meta`
  ADD CONSTRAINT `user_meta_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
