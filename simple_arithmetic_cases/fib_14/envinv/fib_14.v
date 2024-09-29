module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] a,
    output reg [10:0] j,
    output reg [10:0] m
);

    always@(posedge clk) begin
        $display("a: %b, j: %b, m: %b", a, j,m);
    end   
    
    always @(posedge clk) begin
        if(rst)begin
            // w<=1;
            a<= 0;
            m <=300;
            j <=1;
        end
        else begin
            if(selector)begin
                if ((j>m)) begin
                    a <= a;
                    j<=j;
                    m <= m;
                end
                else if ((j<=m))begin
                    m <= m;
                    a <= a  + 1;
                    j <= j + 1;
                end
            end
            else if(!selector) begin
                if ((j<=m)&&(a>0))begin
                    m <= m;
                    a <= a  - 1;
                    j <= j + 1;
                end
                else begin
                    a <= a;
                    j<=j;
                    m <= m;
                end

            end
        end
    end
    // assert property ((j<=m)||((a<=m)&&(a>=0)));
endmodule